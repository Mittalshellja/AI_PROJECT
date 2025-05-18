from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import spacy, uuid, os
import PyPDF2
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="."), name="static")

spacy.cli.download("en_core_web_sm")
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(uploaded_file):
    text = ""
    reader = PyPDF2.PdfReader(uploaded_file.file)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_relationships(text):
    doc = nlp(text)
    edges = []

    for sent in doc.sents:
        for token in sent:
            if token.dep_ in ('nsubj', 'dobj') and token.head.pos_ == 'VERB':
                subject = token.text
                verb = token.head.text
                obj = [child for child in token.head.children if child.dep_ == 'dobj']
                if obj:
                    edges.append((subject, verb + " " + obj[0].text))

    entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "PRODUCT", "WORK_OF_ART"]]
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            edges.append((entities[i], "related_to", entities[j]))

    return edges

def create_graph_image(edges):
    import matplotlib.pyplot as plt
    import networkx as nx
    import uuid

    # Build directed graph
    G = nx.DiGraph()

    for edge in edges:
        if len(edge) == 2:
            G.add_edge(edge[0], edge[1])
        elif len(edge) == 3:
            G.add_edge(edge[0], edge[2], label=edge[1])

    # Remove clutter-causing nodes if needed
    # You can comment this if you want everything
    from collections import Counter
    degree = dict(G.degree())
    high_degree_nodes = [n for n in degree if degree[n] > 15]
    G.remove_nodes_from(high_degree_nodes)

    # Layout
    pos = nx.spring_layout(G, k=0.7, iterations=100, seed=42)

    # Plotting
    plt.figure(figsize=(40, 30))
    nx.draw_networkx_nodes(G, pos, node_size=1800, node_color='skyblue')
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='->', width=1.5, edge_color='gray', connectionstyle="arc3,rad=0.15")
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

    # Draw only selected edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    if edge_labels:
        edge_labels_filtered = {k: v for k, v in edge_labels.items() if len(v) < 20}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_filtered, font_size=7)

    plt.axis('off')
    output_path = f"graph_{uuid.uuid4().hex}.png"
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return output_path

@app.post("/upload/")
async def upload(file: UploadFile = None, text: str = Form(None)):
    if file:
        text_content = extract_text_from_pdf(file)
    elif text:
        text_content = text
    else:
        return {"error": "Please upload a PDF or provide text input."}

    edges = extract_relationships(text_content)
    image_path = create_graph_image(edges)
    return {"image_url": f"/static/{image_path}"}

@app.get("/{image_name}")
def get_image(image_name: str):
    return FileResponse(image_name, media_type="image/png")

