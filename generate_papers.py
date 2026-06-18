from fpdf import FPDF
import os

OUTPUT_DIR = "./papers"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_paper(filename, title, authors, abstract, sections):
    """Create a research paper PDF."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, title, align="C")
    pdf.ln(5)

    # Authors
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 7, authors, align="C")
    pdf.ln(8)

    # Abstract
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Abstract", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, abstract)
    pdf.ln(5)

    # Sections
    for heading, body in sections:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 9, heading, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, body)
        pdf.ln(4)

    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    print(f"Created: {filepath}")


# ── Paper 1: Hierarchical RAG ──────────────────────────────────────────────
paper1_title = "Hierarchical Retrieval-Augmented Generation for Multi-Document Question Answering"
paper1_authors = "John Smith, Alice Wang, Robert Chen\nDepartment of Computer Science, Stanford University"
paper1_abstract = (
    "Retrieval-Augmented Generation (RAG) has emerged as a powerful paradigm for grounding large language models "
    "(LLMs) in external knowledge. However, conventional single-stage retrieval pipelines struggle with complex "
    "queries that require synthesizing information across multiple documents. In this paper, we propose Hierarchical "
    "RAG (H-RAG), a multi-level retrieval framework that first performs coarse-grained document selection and then "
    "applies fine-grained passage extraction before generation. We evaluate H-RAG on three multi-document QA "
    "benchmarks and demonstrate consistent improvements of 8-12% in answer accuracy over flat retrieval baselines. "
    "Our analysis reveals that the hierarchical approach significantly reduces irrelevant context, leading to more "
    "precise and faithful answers."
)
paper1_sections = [
    ("1. Introduction", (
        "Large language models such as GPT-4, LLaMA, and Gemini have demonstrated remarkable capabilities across "
        "a wide range of natural language processing tasks. Despite their strengths, these models are limited by "
        "static training data and are prone to hallucination when asked about information beyond their knowledge "
        "cutoff. Retrieval-Augmented Generation (RAG) addresses this limitation by retrieving relevant documents "
        "from an external corpus and conditioning the generation on the retrieved context.\n\n"
        "While RAG has shown significant promise, most existing implementations rely on a flat retrieval mechanism, "
        "where a single dense retriever fetches the top-k passages from a vector database. This approach has two "
        "key limitations: (1) it treats all passages equally regardless of their source document, and (2) it "
        "struggles to handle queries that require cross-document reasoning. For instance, a question like 'Compare "
        "the climate policies of the EU and the US in 2023' demands retrieving and synthesizing information from "
        "multiple policy documents.\n\n"
        "To address these challenges, we introduce Hierarchical RAG (H-RAG), a two-stage retrieval framework. "
        "In the first stage, a document-level retriever identifies the most relevant documents. In the second stage, "
        "a passage-level retriever extracts the most pertinent paragraphs from the selected documents. This "
        "hierarchical design mirrors human information-seeking behavior, where one first identifies relevant "
        "sources before diving into specific sections."
    )),
    ("2. Related Work", (
        "RAG was first introduced by Lewis et al. (2020), who combined a pre-trained seq2seq model with a dense "
        "passage retriever. Since then, numerous variants have been proposed. FiD (Fusion-in-Decoder) by Izacard "
        "and Grave (2021) processes each retrieved passage independently in the encoder before fusing them in the "
        "decoder. REALM (Guu et al., 2020) jointly pre-trains the retriever and the language model.\n\n"
        "More recently, several works have explored iterative and adaptive retrieval. Self-RAG (Asai et al., 2023) "
        "introduces a self-reflective mechanism that decides when to retrieve and how to use retrieved passages. "
        "FLARE (Jiang et al., 2023) triggers retrieval based on the model's uncertainty during generation.\n\n"
        "Our work differs from these approaches by introducing an explicit hierarchical structure to the retrieval "
        "pipeline, separating document-level and passage-level retrieval into distinct stages with specialized "
        "models for each level."
    )),
    ("3. Methodology", (
        "H-RAG consists of three main components: (1) a Document Retriever, (2) a Passage Retriever, and "
        "(3) a Generator.\n\n"
        "3.1 Document Retriever\n"
        "Given a query q, the document retriever computes a relevance score for each document D in the corpus "
        "using a bi-encoder architecture. Documents are represented by their title and first 512 tokens. The top-M "
        "documents are selected for the next stage. We use a fine-tuned BGE-large model as the document encoder.\n\n"
        "3.2 Passage Retriever\n"
        "Within each selected document, we segment the text into overlapping passages of 256 tokens with a stride "
        "of 128 tokens. A cross-encoder model re-ranks these passages based on their relevance to the query. "
        "The top-K passages across all selected documents are forwarded to the generator.\n\n"
        "3.3 Generator\n"
        "The retrieved passages are concatenated with the query and fed into an instruction-tuned LLM (LLaMA-3 8B). "
        "We use a structured prompt template that encourages the model to cite specific passages and reason step "
        "by step."
    )),
    ("4. Experiments", (
        "We evaluate H-RAG on three multi-document QA benchmarks:\n\n"
        "- MultiRC (Khashabi et al., 2018): A dataset of reading comprehension questions requiring reasoning "
        "over multiple sentences from multiple documents.\n"
        "- HotpotQA (Yang et al., 2018): A multi-hop question answering dataset requiring evidence from two "
        "Wikipedia articles.\n"
        "- MuSiQue (Trivedi et al., 2022): A challenging multi-hop dataset with compositional questions.\n\n"
        "Baselines include standard RAG with flat retrieval, FiD, and Self-RAG. All models use the same "
        "underlying LLM (LLaMA-3 8B) for fair comparison.\n\n"
        "Results show that H-RAG achieves an average improvement of 10.3% in exact match (EM) and 8.7% in F1 "
        "score compared to flat RAG. On HotpotQA, H-RAG achieves 68.4% EM, compared to 59.1% for flat RAG and "
        "63.2% for Self-RAG. The hierarchical retrieval is particularly effective for multi-hop questions, where "
        "identifying the right source documents is crucial."
    )),
    ("5. Analysis and Discussion", (
        "We conduct an ablation study to understand the contribution of each component. Removing the document-level "
        "retrieval (using only passage retrieval) reduces EM by 6.8%, confirming the value of the hierarchical "
        "approach. Replacing the cross-encoder passage re-ranker with a bi-encoder leads to a 3.2% drop in F1.\n\n"
        "Error analysis reveals that the remaining failures are primarily due to (1) ambiguous queries that require "
        "world knowledge not present in the corpus, and (2) very long documents where relevant passages are "
        "scattered across distant sections.\n\n"
        "Latency analysis shows that H-RAG adds approximately 120ms of overhead compared to flat retrieval, "
        "primarily due to the cross-encoder re-ranking step. This is acceptable for most interactive applications."
    )),
    ("6. Conclusion", (
        "We presented Hierarchical RAG, a two-stage retrieval framework for multi-document question answering. "
        "By separating document-level and passage-level retrieval, H-RAG effectively reduces noise in the "
        "retrieved context and enables more accurate cross-document reasoning. Experiments on three benchmarks "
        "demonstrate consistent improvements over existing approaches. Future work will explore extending H-RAG "
        "to multimodal documents and investigating dynamic hierarchies that adapt to query complexity."
    )),
    ("References", (
        "[1] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.\n"
        "[2] Izacard, G. & Grave, E. (2021). Leveraging Passage Retrieval with Generative Models for Open Domain QA. EACL.\n"
        "[3] Guu, K., et al. (2020). REALM: Retrieval-Augmented Language Model Pre-Training. ICML.\n"
        "[4] Asai, A., et al. (2023). Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. NeurIPS.\n"
        "[5] Jiang, Z., et al. (2023). Active Retrieval Augmented Generation. EMNLP.\n"
        "[6] Khashabi, D., et al. (2018). Looking Beyond the Surface: A Challenge Set for Reading Comprehension. NAACL.\n"
        "[7] Yang, Z., et al. (2018). HotpotQA: A Dataset for Diverse, Explainable Multi-hop QA. EMNLP.\n"
        "[8] Trivedi, H., et al. (2022). MuSiQue: Multihop Questions via Single Hop Question Composition. TACL."
    )),
]

# ── Paper 2: Edge Vision Transformers for Agriculture ──────────────────────
paper2_title = "Edge-Optimized Vision Transformers for Real-Time Crop Disease Detection in Precision Agriculture"
paper2_authors = "Maria Garcia, David Kim, Sarah Johnson\nSchool of Agricultural Engineering, UC Davis"
paper2_abstract = (
    "Early detection of crop diseases is critical for reducing agricultural losses and ensuring food security. "
    "While deep learning models have achieved high accuracy in plant disease classification from leaf images, "
    "deploying these models on edge devices in rural farming environments remains challenging due to computational "
    "and memory constraints. In this paper, we present AgriViT, a lightweight Vision Transformer (ViT) architecture "
    "optimized for real-time inference on edge devices such as NVIDIA Jetson Nano and Raspberry Pi 4. We introduce "
    "three key innovations: (1) a dynamic token pruning mechanism that reduces computation by 40% with minimal "
    "accuracy loss, (2) a knowledge distillation pipeline from a large ViT teacher to our compact student model, "
    "and (3) an adaptive quantization scheme for INT8 inference. AgriViT achieves 96.3% accuracy on PlantVillage "
    "and 93.7% on our new CropDisease-50 dataset while running at 28 FPS on Jetson Nano, making it practical "
    "for deployment in real-world agricultural monitoring systems."
)
paper2_sections = [
    ("1. Introduction", (
        "Agriculture remains one of the most critical sectors of the global economy, with crop diseases causing "
        "estimated annual losses of $220 billion worldwide. Traditional disease detection relies on manual "
        "inspection by trained agronomists, which is time-consuming, subjective, and often impractical for "
        "large-scale farming operations.\n\n"
        "Computer vision and deep learning have shown tremendous potential for automated crop disease detection. "
        "Convolutional Neural Networks (CNNs) such as ResNet and EfficientNet have achieved over 99% accuracy "
        "on benchmark datasets like PlantVillage. However, these results are typically obtained on high-end GPUs, "
        "and deploying such models on resource-constrained edge devices poses significant challenges.\n\n"
        "Vision Transformers (ViTs) have recently surpassed CNNs on many image classification tasks. However, "
        "their quadratic attention complexity makes them even more challenging to deploy on edge devices. "
        "Recent works such as DeiT, MobileViT, and EfficientViT have proposed lightweight ViT architectures, "
        "but none have specifically targeted agricultural applications with their unique requirements.\n\n"
        "In this work, we present AgriViT, a purpose-built Vision Transformer for crop disease detection on "
        "edge devices. Our key insight is that leaf disease images contain significant spatial redundancy - "
        "healthy regions of the leaf contribute little to the classification decision. By dynamically pruning "
        "uninformative image tokens during inference, we achieve substantial computational savings without "
        "sacrificing diagnostic accuracy."
    )),
    ("2. Related Work", (
        "2.1 Deep Learning for Plant Disease Detection\n"
        "Mohanty et al. (2016) first demonstrated the feasibility of using deep CNNs for plant disease "
        "identification, achieving 99.35% accuracy on the PlantVillage dataset using GoogLeNet. Subsequent "
        "works have explored various architectures including VGG, ResNet, and DenseNet. Ferentinos (2018) "
        "conducted a comprehensive comparison and found that VGG achieved the best performance.\n\n"
        "2.2 Efficient Vision Transformers\n"
        "DeiT (Touvron et al., 2021) introduced data-efficient training strategies for ViTs, reducing the "
        "data requirements significantly. MobileViT (Mehta & Rastegari, 2022) combined MobileNet blocks with "
        "transformer layers for mobile deployment. EfficientViT (Liu et al., 2023) proposed a cascaded group "
        "attention mechanism for efficient processing.\n\n"
        "2.3 Token Pruning in Transformers\n"
        "DynamicViT (Rao et al., 2021) introduced a learnable token pruning module that progressively removes "
        "less informative tokens. EViT (Liang et al., 2022) fuses uninformative tokens rather than discarding "
        "them. Our approach extends these ideas with domain-specific priors for agricultural images."
    )),
    ("3. Methodology", (
        "3.1 Architecture Overview\n"
        "AgriViT is based on a 6-layer ViT-Tiny backbone with embedding dimension 192 and 3 attention heads. "
        "Input images are split into 16x16 patches, producing 196 tokens for a 224x224 input image. We add a "
        "learnable [CLS] token and sinusoidal positional embeddings.\n\n"
        "3.2 Dynamic Token Pruning\n"
        "After layers 2 and 4, we insert a token selection module that computes an importance score for each "
        "token based on its attention weight relative to the [CLS] token. Tokens with importance scores below "
        "a learned threshold are pruned. For agricultural images, we observe that background and healthy leaf "
        "regions consistently receive low attention scores, validating our pruning strategy.\n\n"
        "During training, we use a soft pruning mechanism with Gumbel-Softmax to maintain differentiability. "
        "At inference, we apply hard pruning for maximum efficiency. The pruning ratio is adaptive: images "
        "with large diseased areas retain more tokens, while images with small lesions prune aggressively.\n\n"
        "3.3 Knowledge Distillation\n"
        "We distill knowledge from a ViT-Base teacher (86M parameters) pre-trained on ImageNet-21k and "
        "fine-tuned on our agricultural datasets. The distillation loss combines: (1) KL divergence between "
        "teacher and student logits (temperature=4), (2) MSE loss on intermediate feature maps, and "
        "(3) attention transfer loss that aligns the student's attention patterns with the teacher's.\n\n"
        "3.4 Quantization-Aware Training\n"
        "We apply quantization-aware training (QAT) to prepare the model for INT8 inference. We use per-channel "
        "quantization for weights and per-tensor quantization for activations. Special care is taken to quantize "
        "the softmax operation in attention layers using a lookup table approach."
    )),
    ("4. Experiments", (
        "4.1 Datasets\n"
        "- PlantVillage: 54,305 images of 38 disease classes across 14 crop species.\n"
        "- CropDisease-50: Our new dataset containing 125,000 images of 50 disease classes across 20 crops, "
        "collected from farms in California, India, and Brazil. Images were captured using smartphone cameras "
        "under diverse lighting and background conditions.\n\n"
        "4.2 Implementation Details\n"
        "All models are trained for 100 epochs using AdamW optimizer with a cosine learning rate schedule "
        "(initial LR=1e-3, weight decay=0.05). Data augmentation includes random resized crop, horizontal flip, "
        "color jitter, and RandAugment. Training is performed on 4 NVIDIA A100 GPUs.\n\n"
        "4.3 Results\n"
        "On PlantVillage, AgriViT achieves 96.3% top-1 accuracy with only 5.2M parameters, compared to 96.8% "
        "for the full ViT-Base (86M parameters) and 95.1% for MobileViT-S (5.6M parameters). On CropDisease-50, "
        "AgriViT achieves 93.7%, outperforming MobileViT-S (91.2%) and EfficientNet-B0 (92.4%).\n\n"
        "4.4 Edge Deployment Results\n"
        "On NVIDIA Jetson Nano, AgriViT (INT8) achieves 28 FPS with 96.1% accuracy (only 0.2% drop from FP32). "
        "On Raspberry Pi 4, it achieves 8.3 FPS. MobileViT-S achieves only 19 FPS on Jetson Nano, demonstrating "
        "the effectiveness of our token pruning approach. The model requires only 12MB of storage in INT8 format."
    )),
    ("5. Field Deployment Case Study", (
        "We deployed AgriViT on a network of 15 Jetson Nano devices across three tomato farms in Salinas Valley, "
        "California. Each device was connected to a 12MP camera mounted on an automated rail system that traverses "
        "crop rows. The system captures images every 30 seconds and runs inference locally.\n\n"
        "Over a 4-month growing season (June-September 2025), the system processed 2.1 million images and "
        "detected 847 disease instances, including early blight, late blight, and bacterial spot. The average "
        "detection latency was 35ms per image. When compared to weekly manual inspections, our system detected "
        "diseases an average of 3.2 days earlier, allowing farmers to apply targeted treatments and reducing "
        "fungicide usage by 31%.\n\n"
        "Farmers reported high satisfaction with the system, particularly appreciating the real-time alerts "
        "sent to their smartphones when disease was detected. The false positive rate was 4.7%, which farmers "
        "considered acceptable."
    )),
    ("6. Conclusion", (
        "We presented AgriViT, a lightweight Vision Transformer optimized for real-time crop disease detection "
        "on edge devices. Through dynamic token pruning, knowledge distillation, and adaptive quantization, "
        "AgriViT achieves near state-of-the-art accuracy while running at practical frame rates on low-cost "
        "hardware. Our field deployment demonstrates the real-world viability of the approach.\n\n"
        "Future work will extend AgriViT to multi-spectral imaging (combining RGB with near-infrared data), "
        "incorporate temporal modeling for disease progression tracking, and explore federated learning to "
        "enable privacy-preserving model updates across multiple farms."
    )),
    ("References", (
        "[1] Mohanty, S.P., et al. (2016). Using Deep Learning for Image-Based Plant Disease Detection. Frontiers in Plant Science.\n"
        "[2] Ferentinos, K.P. (2018). Deep Learning Models for Plant Disease Detection and Diagnosis. Computers and Electronics in Agriculture.\n"
        "[3] Touvron, H., et al. (2021). Training Data-Efficient Image Transformers & Distillation Through Attention. ICML.\n"
        "[4] Mehta, S. & Rastegari, M. (2022). MobileViT: Light-weight, General-purpose, and Mobile-friendly Vision Transformer. ICLR.\n"
        "[5] Liu, X., et al. (2023). EfficientViT: Memory Efficient Vision Transformer with Cascaded Group Attention. CVPR.\n"
        "[6] Rao, Y., et al. (2021). DynamicViT: Efficient Vision Transformers with Dynamic Token Sparsification. NeurIPS.\n"
        "[7] Liang, Y., et al. (2022). Not All Patches are What You Need: Expediting Vision Transformers via Token Reorganizations. ICLR."
    )),
]


if __name__ == "__main__":
    create_paper(
        "research_paper_1_hierarchical_rag.pdf",
        paper1_title, paper1_authors, paper1_abstract, paper1_sections,
    )
    create_paper(
        "research_paper_2_edge_vit_agriculture.pdf",
        paper2_title, paper2_authors, paper2_abstract, paper2_sections,
    )
    print("\nDone! 2 papers created in ./papers/")
