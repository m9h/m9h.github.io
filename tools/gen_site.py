#!/usr/bin/env python3
"""Generate index.html from the GitHub repo dump (tools/repos.tsv).

Refresh the dump, then rebuild:
  gh api --paginate "users/m9h/repos?per_page=100&type=owner" --jq '.[] | select(.fork==false and .archived==false) | [.name, (.stargazers_count|tostring), (.language // "-"), .pushed_at[:10], (.description // ""), (.topics|join(","))] | @tsv' > tools/repos.tsv
  python3 tools/gen_site.py index.html
"""
import csv, html, sys, re
from pathlib import Path

HERE = Path(__file__).parent
OUT = Path(sys.argv[1])

repos = {}
with open(HERE / "repos.tsv", newline="") as f:
    for row in csv.reader(f, delimiter="\t"):
        name, stars, lang, pushed, desc, topics = (row + [""] * 6)[:6]
        repos[name] = dict(stars=int(stars or 0), lang=lang, pushed=pushed, desc=desc)

def short(desc, n=120):
    desc = desc.strip()
    # first sentence / clause, then hard cap
    m = re.split(r"(?<=[.;])\s|\s[—–]\s", desc, maxsplit=1)
    s = m[0] if m and len(m[0]) >= 30 else desc
    if len(s) > n:
        s = s[: n - 1].rsplit(" ", 1)[0] + "…"
    return s.rstrip(";:,. ") if not s.endswith("…") else s

OVERRIDES = {
    "brain-fwi": "Full-waveform inversion for transcranial ultrasound in JAX, with neural-operator surrogates",
    "devograph": "Developmental neurobiology extensions for hgx: dynamics, geometric convolutions, optimal transport, C. elegans tooling",
    "hgx": "Hypergraph neural networks in JAX/Equinox: topological and geometric deep learning on higher-order domains",
    "anatomical-compiler": "Engineering fully-biologic tissue systems: a hypergraph instrument for synthetic morphology and multicellularity",
    "fijee": "Forward modelling with FEM for EEG, with DataLad-managed FSL, FreeSurfer, TRACULA, and MNE",
}

def row(name, override=None, kind=None):
    r = repos.get(name, {})
    if override is None:
        override = OVERRIDES.get(name)
    desc = override if override is not None else short(r.get("desc", ""))
    lang = kind or r.get("lang", "-")
    if lang == "-":
        lang = ""
    return (
        f'<a class="row" href="https://github.com/m9h/{name}">'
        f'<span class="k">{html.escape(name)}</span>'
        f'<span class="v">{html.escape(desc)}</span>'
        f'<span class="t">{html.escape(lang)}</span></a>'
    )

GROUPS = [
    ("Differentiable neuroimaging in JAX",
     "Forward models, inverse solvers, and simulation-based inference for EEG, MEG, MRI, MRS, fNIRS, and ultrasound.",
     ["neurojax", "brain-fwi", "ti-sim", "inferjax", "dot-jax", "mrs-jax", "hnn-jax", "gnf-jax",
      "hippy-feat", "neuroelectric-mri", "mri-rf-stack", "fem-trials"]),
    ("Brain dynamics, active inference, agents",
     "Neural mass and physiology models, spiking cultures, active inference, and the control theory under them.",
     ["alf", "bl1", "vpjax", "vc2008-netpyne", "neuro-dynadojo", "jaxctrl", "hgx", "devograph",
      "neurosim", "SustainHub-jaxmarl", "agentsciml", "qc-computational-cognitive-modeling"]),
    ("Interpretability and reasoning",
     "Controls, null distributions, and replications for claims about what models are doing inside.",
     ["jlens-lab", "tri-lens", "controls-and-trajectories", "societies-of-thought",
      "self-report-validity", "wwj", "neural-decoding-transfer"]),
    ("Spinning Up curricula",
     "Module-by-module courses, each one a runnable repo.",
     ["spinning-up-alf", "spinning-up-in-pde", "spinning-up-in-mech-interp", "spinning-up-in-openscope"]),
    ("Open hardware and wet lab",
     "EEG acquisition, lab instruments, bioreactors, and the Biopunk Lab projects.",
     ["freeeeg128", "open-alliance-daq", "ato-heater-pid", "ato-qcm-monitor", "biopunk-bioreactor",
      "biopunk-jubilee", "biopunk-duckweed", "biopunk-artbot", "biopunk-display", "bsccm-jax",
      "anatomical-compiler", "biohub-starter"]),
    ("Structural biology",
     "Conformational landscapes and DNA nanostructures inside UCSF ChimeraX.",
     ["chimerax-vampnet", "chimerax-origami"]),
    ("Packaging and infrastructure",
     "Getting neuroscience software to build, install, and run on Fedora, Debian, macOS, and arm64.",
     ["neurofedora", "neurodebian", "homebrew-neuro", "neurocontainers-arm", "fedora-afni-desktop-integration",
      "fedora-linear-algebra-mag-series", "charm-gems-cli", "insula", "libspm", "nsg-agent-kit",
      "research-infra", "autonomic"]),
    ("Origins, 2017",
     "The first Center17 effort: FEM forward modelling for EEG with FreeSurfer, FSL, TRACULA, and MNE via DataLad.",
     ["fijee", "infocypher-scieng-deps", "valis"]),
]

missing = [n for _, _, ns in GROUPS for n in ns if n not in repos]
if missing:
    sys.exit(f"not in repos.tsv: {missing}")

PINNED = [
    ("alf", "Active Inference/Learning Framework: standalone JAX-native active inference for discrete POMDPs"),
    ("spinning-up-alf", "Spinning Up in Active Inference: 16-module curriculum bridging RL and active inference in JAX"),
    ("anatomical-compiler", "A hypergraph network instrument for synthetic morphology, toward Levin's anatomical compiler"),
    ("bl1", "In-silico cortical culture simulator: JAX spiking network with STDP, virtual MEA, closed-loop games"),
    ("neurojax", "JAX-accelerated electrophysiology analysis with MNE, Diffrax, and osl-dynamics integration"),
    ("sbi4dwi", "Open-source toolbox for reproducible diffusion MRI microstructure estimation"),
]

sections = []
for title, lede, names in GROUPS:
    rows = "\n      ".join(row(n) for n in names)
    sections.append(f"""
    <section class="section">
      <h2>{html.escape(title)}</h2>
      <p class="lede">{html.escape(lede)}</p>
      {rows}
    </section>""")

pinned_rows = "\n      ".join(row(n, override=d) for n, d in PINNED)
n_repos = len(repos)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Morgan Hough</title>
  <meta name="description" content="Morgan Hough, San Francisco. Developmental neurobiology at OREL, community manager at NeuroTechX, neurotech lead at Frontier Tower, R&amp;D at Biopunk Lab. Code as m9h, models and data as mhough, writing at center17.org.">
  <link rel="me" href="https://github.com/m9h">
  <link rel="me" href="https://huggingface.co/mhough">
  <link rel="me" href="https://bsky.app/profile/mhough.bsky.social">
  <link rel="me" href="https://www.linkedin.com/in/morgan-g-hough">
  <link rel="me" href="https://twitter.com/mhough">
  <style>
    @font-face {{
      font-family: 'System';
      src: local('Iosevka'), local('PragmataPro'), local('IBM Plex Mono'), local('SF Mono'), local('Menlo'), local('Consolas');
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      background: #111111; color: #d4d4d4;
      font-family: 'Palatino Linotype', Palatino, 'Book Antiqua', Georgia, serif;
      font-size: 17px; line-height: 1.7; -webkit-font-smoothing: antialiased;
    }}
    ::selection {{ background: #c8102e; color: #fff; }}
    a {{ color: inherit; text-decoration: none; border-bottom: 1px solid #555; transition: border-color 0.15s; }}
    a:hover {{ border-bottom-color: #c8102e; }}
    .mono {{ font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace; }}

    .topnav {{
      position: sticky; top: 0; z-index: 10;
      background: rgba(17,17,17,0.94); backdrop-filter: blur(6px); border-bottom: 1px solid #2a2a2a;
    }}
    .topnav .inner {{
      max-width: 1000px; margin: 0 auto; padding: 14px 32px;
      display: flex; align-items: baseline; gap: 24px; flex-wrap: wrap;
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.14em;
    }}
    .topnav a {{ border-bottom: none; color: #999; }}
    .topnav a:hover {{ color: #d4d4d4; }}
    .topnav .brand {{ color: #d4d4d4; margin-right: 8px; }}
    .topnav .brand b {{ color: #c8102e; }}
    .topnav .ext {{ margin-left: auto; }}
    .topnav .ext::after {{ content: " \\2197"; }}

    .page {{ max-width: 1000px; margin: 0 auto; padding: 56px 32px 80px; }}

    .masthead {{
      display: grid; grid-template-columns: 1fr 320px; gap: 40px; align-items: end;
      padding-bottom: 40px; border-bottom: 3px solid #d4d4d4; margin-bottom: 52px;
    }}
    .masthead h1 {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 2.8rem; font-weight: 400; letter-spacing: 0.06em; line-height: 1.1; margin-bottom: 10px;
    }}
    .masthead h1 b {{ color: #c8102e; font-weight: 700; }}
    .handle {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 0.78rem; letter-spacing: 0.14em; text-transform: lowercase; color: #888;
    }}
    .masthead .lede {{ font-style: italic; color: #999; max-width: 520px; margin-top: 16px; font-size: 1rem; }}
    .masthead .lede a {{ color: #bbb; }}
    .masthead .now {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 0.74rem; line-height: 1.9; color: #888;
    }}
    .masthead .now dt {{ text-transform: uppercase; letter-spacing: 0.14em; font-size: 0.62rem; color: #666; margin-top: 8px; }}
    .masthead .now dd {{ margin: 0; }}
    .masthead .now a {{ color: #bbb; }}

    .section {{ margin-bottom: 52px; scroll-margin-top: 64px; }}
    .section h2 {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 1.15rem; font-weight: 400; letter-spacing: 0.06em; margin-bottom: 4px;
    }}
    .section .lede {{ font-style: italic; color: #888; max-width: 640px; margin-bottom: 18px; font-size: 0.95rem; }}
    .section .lede a {{ color: #bbb; }}
    .row {{
      display: grid; grid-template-columns: 220px 1fr 90px; gap: 16px;
      padding: 9px 0; border-bottom: 1px dotted #2a2a2a; align-items: baseline;
    }}
    .row:last-child {{ border-bottom: none; }}
    .row:hover .k {{ color: #c8102e; }}
    .k {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 0.86rem; font-weight: 700; transition: color 0.15s; overflow-wrap: anywhere;
    }}
    .v {{ font-size: 0.88rem; color: #999; }}
    .v a {{ color: #bbb; }}
    .t {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 0.68rem; color: #777; text-align: right; white-space: nowrap;
    }}
    .affil .row {{ grid-template-columns: 220px 1fr; }}
    .affil .v em {{ color: #bbb; font-style: normal; }}
    .prose {{ color: #aaa; max-width: 640px; }}
    .prose p + p {{ margin-top: 12px; }}
    .prose a {{ color: #ccc; }}

    footer {{
      margin-top: 56px; padding-top: 20px; border-top: 3px solid #d4d4d4;
      display: flex; justify-content: space-between; align-items: baseline; gap: 20px; flex-wrap: wrap;
      font-size: 0.78rem; color: #888;
    }}
    footer nav {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    footer nav a {{
      font-family: 'System', 'IBM Plex Mono', 'SF Mono', Menlo, Consolas, monospace;
      font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #888; border-bottom: none;
    }}
    footer nav a:hover {{ color: #c8102e; }}

    @media (max-width: 700px) {{
      .topnav .inner {{ padding: 12px 20px; gap: 14px; }}
      .topnav .ext {{ margin-left: 0; }}
      .page {{ padding: 40px 20px 60px; }}
      .masthead {{ grid-template-columns: 1fr; }}
      .masthead h1 {{ font-size: 2.1rem; }}
      .row, .affil .row {{ grid-template-columns: 1fr; gap: 2px; }}
      .t {{ text-align: left; }}
    }}
  </style>
</head>
<body>
<nav class="topnav"><div class="inner">
  <a class="brand" href="#">morgan <b>hough</b></a>
  <a href="#affiliations">Affiliations</a>
  <a href="#pinned">Pinned</a>
  <a href="#code">Code</a>
  <a href="#center17">Center17</a>
  <a class="ext" href="https://github.com/m9h">github.com/m9h</a>
</div></nav>

<div class="page">

  <header class="masthead">
    <div>
      <h1>Morgan <b>Hough</b></h1>
      <div class="handle">san francisco &middot; m9h on github &middot; mhough on hugging face, bluesky, x</div>
      <p class="lede">Developmental neurobiology, neurotechnology, and open hardware. Most of the research lives at <a href="https://center17.org/">Center17</a>, demi-human cybernetics; the code is below.</p>
    </div>
    <dl class="now">
      <dt>Code</dt><dd><a href="https://github.com/m9h">github.com/m9h</a> &middot; <a href="https://gitlab.com/center17">gitlab.com/center17</a></dd>
      <dt>Models &amp; data</dt><dd><a href="https://huggingface.co/mhough">huggingface.co/mhough</a></dd>
      <dt>Social</dt><dd><a href="https://bsky.app/profile/mhough.bsky.social">bluesky</a> &middot; <a href="https://twitter.com/mhough">x</a> &middot; <a href="https://www.linkedin.com/in/morgan-g-hough">linkedin</a> &middot; <a href="https://t.me/s/mhough">telegram</a></dd>
      <dt>Writing</dt><dd><a href="https://center17.org/">center17.org</a></dd>
    </dl>
  </header>

  <section class="section affil" id="affiliations">
    <h2>Affiliations</h2>
    <p class="lede">As listed on the GitHub profile.</p>
    <a class="row" href="https://github.com/OREL-group"><span class="k">OREL</span><span class="v"><em>Developmental Neurobiology.</em> Orthogonal Research &amp; Education Lab, a distributed open-science lab in computational biology, neuroscience, and cognition.</span></a>
    <a class="row" href="https://neurotechx.com/"><span class="k">NeuroTechX</span><span class="v"><em>Community Manager.</em> The volunteer-led global community of neurotechnology innovators.</span></a>
    <a class="row" href="https://berlinhouse.com/"><span class="k">Frontier Tower</span><span class="v"><em>Neurotech Lead.</em> Berlin House's self-organized community lab for frontier tech in San Francisco.</span></a>
    <a class="row" href="https://github.com/m9h?tab=repositories&q=biopunk"><span class="k">Biopunk Lab</span><span class="v"><em>Research and Development.</em> Open bioreactors, bioassays, liquid handling, and living art.</span></a>
  </section>

  <section class="section" id="pinned">
    <h2>Pinned</h2>
    <p class="lede">The six repositories pinned on the profile.</p>
    {pinned_rows}
  </section>

  <div id="code"></div>
  {"".join(sections)}

  <section class="section" id="center17">
    <h2>Center17</h2>
    <p class="lede">The lab site, its project index, and its reading river.</p>
    <a class="row" href="https://center17.org/"><span class="k">center17.org</span><span class="v">Blog and about page</span><span class="t">ghost</span></a>
    <a class="row" href="https://projects.center17.org/"><span class="k">projects.center17.org</span><span class="v">Index of code, data, and models across the lab's repositories</span><span class="t">gitlab pages</span></a>
    <a class="row" href="https://river.center17.org/"><span class="k">river.center17.org</span><span class="v">Blogroll river, newest first, with an events calendar</span><span class="t">gitlab pages</span></a>
  </section>

  <footer>
    <span>&copy; Morgan Hough &middot; {n_repos} original repositories on GitHub</span>
    <nav>
      <a href="https://github.com/m9h/m9h.github.io">source</a>
      <a href="https://github.com/m9h">github</a>
      <a href="https://huggingface.co/mhough">hugging face</a>
      <a href="https://center17.org/">center17</a>
    </nav>
  </footer>

</div>
</body>
</html>
"""
OUT.write_text(page)
print(f"wrote {OUT} ({len(page)} bytes, {n_repos} repos, {sum(len(g[2]) for g in GROUPS)} listed)")
