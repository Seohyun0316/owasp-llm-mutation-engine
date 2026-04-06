import random

from src.operators.op_fmt_html_document_embedding import apply


SEED = "A < B"

EXPECTED_S1 = "<html><body>A &lt; B</body></html>"

EXPECTED_S2 = (
    "<!DOCTYPE html>\n"
    "<html>\n"
    "  <head>\n"
    "    <title>Document</title>\n"
    "  </head>\n"
    "  <body>\n"
    "    <p>A &lt; B</p>\n"
    "  </body>\n"
    "</html>"
)

EXPECTED_S3 = (
    "<!DOCTYPE html>\n"
    "<html>\n"
    "  <head>\n"
    "    <title>Internal Page</title>\n"
    "  </head>\n"
    "  <body>\n"
    "    <!-- embedded content block -->\n"
    "    <section>\n"
    "      <article>\n"
    "        <p>A &lt; B</p>\n"
    "      </article>\n"
    "    </section>\n"
    "  </body>\n"
    "</html>"
)

EXPECTED_S4 = (
    "<!DOCTYPE html>\n"
    "<html lang=\"en\">\n"
    "  <head>\n"
    "    <meta charset=\"utf-8\" />\n"
    "    <meta name=\"document-type\" content=\"internal-note\" />\n"
    "    <title>Operational Memo</title>\n"
    "  </head>\n"
    "  <body>\n"
    "    <div class=\"page\">\n"
    "      <section class=\"content\">\n"
    "        <article data-role=\"embedded-text\">\n"
    "          <p>A &lt; B</p>\n"
    "        </article>\n"
    "      </section>\n"
    "    </div>\n"
    "  </body>\n"
    "</html>"
)

EXPECTED_S5 = (
    "<!DOCTYPE html>\n"
    "<html lang=\"en\">\n"
    "  <head>\n"
    "    <meta charset=\"utf-8\" />\n"
    "    <meta name=\"source\" content=\"mail-archive\" />\n"
    "    <meta name=\"processing-mode\" content=\"document-first\" />\n"
    "    <title>Archived HTML Message</title>\n"
    "  </head>\n"
    "  <body>\n"
    "    <!-- start archived content -->\n"
    "    <div id=\"container\" data-kind=\"message\">\n"
    "      <header>\n"
    "        <h1>Embedded Message</h1>\n"
    "      </header>\n"
    "      <main>\n"
    "        <section class=\"thread\">\n"
    "          <article class=\"entry\" data-priority=\"high\">\n"
    "            <div class=\"content-block\">\n"
    "              <p>A &lt; B</p>\n"
    "            </div>\n"
    "          </article>\n"
    "        </section>\n"
    "      </main>\n"
    "      <footer>\n"
    "        <small>end-of-message</small>\n"
    "      </footer>\n"
    "    </div>\n"
    "    <!-- end archived content -->\n"
    "  </body>\n"
    "</html>"
)


def test_html_document_embedding_s1_strength1_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 1}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S1


def test_html_document_embedding_s2_strength2_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 2}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S2


def test_html_document_embedding_s3_strength3_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 3}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S3


def test_html_document_embedding_s4_strength4_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 4}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S4


def test_html_document_embedding_s5_strength5_ok():
    r = apply(SEED, {"surface": "PROMPT_TEXT", "strength": 5}, random.Random(0))
    assert r.status == "OK"
    assert r.child_text == EXPECTED_S5