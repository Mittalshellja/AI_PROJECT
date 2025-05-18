from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import spacy, uuid, os
import PyPDF2
import networkx as nx
import matplotlib.pyplot as plt

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory to serve images
STATIC_DIR = "static"
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Load spaCy model
spacy.cli.download("en_core_web_sm")  # optional if already downloaded
nlp = spacy.load("en_core_web_sm")

# PDF text extraction
def extract_text_from_pdf(uploaded_file):
    text = ""
    reader = PyPDF2.PdfReader(uploaded_file.file)
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# NLP-based relationship extraction
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
                    edges.append((subject, f"{verb} {obj[0].text}"))

    entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "PRODUCT", "WORK_OF_ART"]]
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            edges.append((entities[i], "related_to", entities[j]))

    return edges

# Graph generation and saving
def create_graph_image(edges):
    try:
        G = nx.DiGraph()

        for edge in edges:
            if len(edge) == 2:
                G.add_edge(edge[0], edge[1])
            elif len(edge) == 3:
                G.add_edge(edge[0], edge[2], label=edge[1])

        # Remove clutter: nodes with too many connections
        degree = dict(G.degree())
        high_degree_nodes = [n for n in degree if degree[n] > 15]
        G.remove_nodes_from(high_degree_nodes)

        pos = nx.spring_layout(G, k=0.7, iterations=100, seed=42)

        plt.figure(figsize=(40, 30))
        nx.draw_networkx_nodes(G, pos, node_size=1800, node_color='skyblue')
        nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle='->', width=1.5, edge_color='gray', connectionstyle="arc3,rad=0.15")
        nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

        edge_labels = nx.get_edge_attributes(G, 'label')
        if edge_labels:
            edge_labels_filtered = {k: v for k, v in edge_labels.items() if len(v) < 20}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_filtered, font_size=7)

        plt.axis('off')
        plt.tight_layout()

        filename = f"graph_{uuid.uuid4().hex}.png"
        output_path = os.path.join(STATIC_DIR, filename)
        plt.savefig(output_path)
        plt.close()
        return filename
    except Exception as e:
        print("Failed to generate graph:", e)
        return None

# Upload endpoint (PDF or text)
@app.post("/upload/")
async def upload(file: UploadFile = None, text: str = Form(None)):
    if file:
        text_content = extract_text_from_pdf(file)
    elif text:
        text_content = text
    else:
        return {"error": "Please upload a PDF or provide text input."}

    edges = extract_relationships(text_content)
    image_name = create_graph_image(edges)

    if image_name:
        return {"image_url": f"/static/{image_name}"}
    else:
        return {"error": "Failed to generate graph."}

# Endpoint to retrieve image directly
@app.get("/{image_name}")
def get_image(image_name: str):
    image_path = os.path.join(STATIC_DIR, image_name)
    return FileResponse(image_path, media_type="image/png")


# Run the app with: uvicorn main:app --reload