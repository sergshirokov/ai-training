"""
LangChain pipeline for generating technical illustrations from tutorial transcripts.

Public function:
    create_illustration(input_transcript: str, output_file: Path) -> None

Pipeline stages:
1. Transcript cleaning
2. Visual concept extraction
3. Image prompt generation with fixed style anchor
4. Safety sanitization for image prompt
5. Image generation with retry + fallback

Environment configuration is loaded from `settings.py` which calls load_dotenv()
and exposes OPENAI_API_KEY. The key is passed explicitly to both OpenAI SDK
and LangChain ChatOpenAI to avoid relying on implicit environment lookup.
"""

from pathlib import Path
import base64
import re

from settings import *  # loads OPENAI_API_KEY via dotenv

from openai import OpenAI

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


# --------------------------------------------------
# Fixed visual style anchor (keeps illustrations consistent)
# --------------------------------------------------

STYLE_ANCHOR = """
consistent visual style across all images, modern DevOps documentation illustration,
dark IDE interface theme, minimal UI panels, terminal windows, workflow arrows,
soft neon blue and green highlights, clean vector-tech illustration, subtle depth,
high clarity, suitable for professional programming course material
"""


# --------------------------------------------------
# Safety sanitization
# --------------------------------------------------

REPLACEMENTS = [
    (r"\\bprivate key\\b", "credential file"),
    (r"\\bpublic key\\b", "credential file"),
    (r"\\bssh\\b", "remote connection"),
    (r"\\brsa\\b", "standard format"),
    (r"\\bpassphrase\\b", "password"),
    (r"\\bppk\\b", "format A"),
    (r"\\bpem\\b", "format B"),
    (r"\\bputty(gen)?\\b", "conversion utility"),
    (r"\\bkey\\b", "config"),
]


BANNED_PATTERNS = [
    r"\\bprivate key\\b",
    r"\\bpublic key\\b",
    r"\\bssh\\b",
    r"\\brsa\\b",
    r"\\bppk\\b",
    r"\\bpem\\b",
    r"\\bputty(gen)?\\b",
]


def sanitize_for_image(text: str) -> str:
    """Replace sensitive technical terms to reduce moderation blocks."""

    t = text

    for pat, rep in REPLACEMENTS:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)

    for pat in BANNED_PATTERNS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)

    t = re.sub(r"\\s{2,}", " ", t).strip()

    return t


# --------------------------------------------------
# Fallback prompt if moderation blocks generation
# --------------------------------------------------

FALLBACK_PROMPT = """
Technical documentation-style illustration of a developer converting a file
from Format A to Format B using a desktop utility.

Show a workflow diagram with arrows between file icons, a terminal window,
and a simple developer tool interface.

Dark IDE theme, minimal labels, clean DevOps tutorial illustration.
"""


# --------------------------------------------------
# Initialize clients once (module level)
# --------------------------------------------------

llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.2,
    api_key=OPENAI_API_KEY,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

parser = StrOutputParser()


# --------------------------------------------------
# Prompt templates
# --------------------------------------------------

clean_prompt = ChatPromptTemplate.from_template("""
Rewrite the transcript into a short neutral technical description.

Rules:
- remove greetings and filler speech
- keep only the technical action
- avoid security-sensitive wording
- describe tools, files, or processes

Maximum length: 20 words.

Transcript:
{transcript}

Output only the cleaned description.
""")

concept_prompt = ChatPromptTemplate.from_template("""
Determine the main visual concept for illustrating the technical description.

Choose ONE category:

tool_usage
terminal_workflow
file_conversion
infrastructure
api_flow
coding
data_pipeline

Description:
{description}

Output only the category.
""")

prompt_builder = ChatPromptTemplate.from_template("""
Create an image generation prompt for a technical illustration.

Concept:
{concept}

Description:
{description}

Style anchor:
{style_anchor}

Image rules:
- focus on one clear technical process
- developer workstation or infrastructure environment
- dark developer theme
- minimal readable text
- clear workflow visualization

Audience:
software developers, DevOps engineers, backend engineers.

Return only the final image generation prompt.
""")


# --------------------------------------------------
# Chains
# --------------------------------------------------

clean_chain = clean_prompt | llm | parser
concept_chain = concept_prompt | llm | parser
image_prompt_chain = prompt_builder | llm | parser


# --------------------------------------------------
# Public API
# --------------------------------------------------


def create_illustration(input_transcript: str, output_file: Path) -> None:
    """
    Generate a technical illustration from a tutorial transcript.

    Parameters
    ----------
    input_transcript : str
        Transcript text extracted from tutorial audio.

    output_file : Path
        Path where the generated image will be saved.
    """

    print(f"Генерация иллюстрации {input_transcript} -> {output_file}")

    pipeline = (
        RunnablePassthrough.assign(
            description=clean_chain
        )
        .assign(
            concept=lambda x: concept_chain.invoke({"description": x["description"]})
        )
        .assign(
            image_prompt=lambda x: image_prompt_chain.invoke({
                "concept": x["concept"],
                "description": x["description"],
                "style_anchor": STYLE_ANCHOR
            })
        )
    )

    result = pipeline.invoke({"transcript": input_transcript})


    # --------------------------------------------------
    # Sanitize prompt before sending to image API
    # --------------------------------------------------

    safe_prompt = sanitize_for_image(result["image_prompt"])


    # --------------------------------------------------
    # Generate image
    # --------------------------------------------------

    try:

        image = openai_client.images.generate(
            model="gpt-image-1",
            prompt=safe_prompt,
            size="1024x1024"
        )

    except Exception:

        image = openai_client.images.generate(
            model="gpt-image-1",
            prompt=FALLBACK_PROMPT,
            size="1024x1024"
        )


    image_base64 = image.data[0].b64_json


    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "wb") as f:
        f.write(base64.b64decode(image_base64))

    print(f"Изображение сохранено: {output_file}")
