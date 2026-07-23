# Excalidraw Libraries / offline mirror

A self-hosted copy of [Excalidraw](https://excalidraw.com) component libraries for
**GCP, software/system architecture, and networking** diagrams.

Mirror in case corporate proxy blocks `libraries.excalidraw.com`. All files
are the original `.excalidrawlib` JSON from
[`excalidraw/excalidraw-libraries`](https://github.com/excalidraw/excalidraw-libraries)
(MIT-licensed; each library keeps its original author — see attribution below).

## How to use (offline / no proxy needed)

You do **not** need the online library browser. Import the files directly:

1. Download the `.excalidrawlib` file you want from this repo (or `git clone` the whole repo).
2. Open Excalidraw (excalidraw.com, the desktop app, or a self-hosted instance).
3. Open the **Library panel** - the book/grid icon in the top-right toolbar.
4. **Drag-and-drop the `.excalidrawlib` file** onto the Excalidraw window.
   *(Alternative: Library panel → the `⋯`/hamburger menu → **Open** → pick the file.)*
5. The components appear in your library, ready to drag onto the canvas. Repeat for
   each file - imported libraries stack, so you can load several.

> Tip: your imported libraries persist in that browser/profile, so you only import once
> per machine. To move them between machines, just re-import the files.

### If `raw.githubusercontent.com` IS reachable on your network
You can one-click load any file via the `addLibrary` URL, e.g.:
```
https://excalidraw.com/?addLibrary=https://raw.githubusercontent.com/andreasbros/excalidraw/main/gcp/gcp-icons.excalidrawlib
```
(If GitHub raw is also blocked, use the drag-and-drop method above.)

## Finding a specific component

The library panel is just tiny thumbnails with no search, and **many icons (all the GCP
ones) have no name**, so hovering won't help. Two ways to find what you need:

**1. Visual catalogues (best — works for unnamed icons).**
Every library has a companion scene in [`catalogues/`](catalogues) that lays out *all* its
components in a labelled grid (`#index  name`). Open the matching
`catalogues/<category>/<name>.excalidraw` in Excalidraw (drag-drop or Open), zoom in to
read them at full size, then **copy the icon you want (Ctrl+C) and paste it straight into
your diagram** — you don't even need the library panel. It doubles as a visual palette.

**2. Text index (for the ~60% that are named).**
[`INDEX.md`](INDEX.md) lists every *named* component grouped by library — **Ctrl+F** for
e.g. "Cloud Run", see which file it's in, import that file.

**UI tips inside Excalidraw:**
- Hover an item to see its name (if it has one).
- Zoom the whole browser (**Ctrl +**) to enlarge the tiny library thumbnails.
- Import **one** library at a time while hunting to cut clutter; remove it after.

## Libraries included

### `gcp/` - Google Cloud Platform
| File | Items | What |
|---|---|---|
| `gcp-icons.excalidrawlib` | 83 | GCP product/service icons |
| `original-google-architecture-icons.excalidrawlib` | 139 | Official Google Cloud architecture icon set |
| `google-icons.excalidrawlib` | 139 | Broader Google product icons |

### `architecture/` - software & system design
| File | Items | What |
|---|---|---|
| `software-architecture.excalidrawlib` | 7 | Software architecture building blocks |
| `architecture-diagram-components.excalidrawlib` | 11 | Generic architecture diagram components |
| `system-design.excalidrawlib` | 24 | System design components |
| `systemdesignicons.excalidrawlib` | 3 | System design icons |
| `system-design-template.excalidrawlib` | 8 | System design template pieces |
| `c4-architecture.excalidrawlib` | 10 | C4 model (context/container/component) |
| `db-eng.excalidrawlib` | 39 | Database / data engineering shapes |

### `network/` - network & infrastructure
| File | Items | What |
|---|---|---|
| `network-topology-icons.excalidrawlib` | 10 | Network topology icons |
| `network-elements.excalidrawlib` | 5 | Network elements |
| `racks-and-servers-components.excalidrawlib` | 5 | Racks & server components |
| `network-locations.excalidrawlib` | 5 | Network location markers |

### `cloud-k8s-devops/` - cloud-neutral, Kubernetes, DevOps
| File | Items | What |
|---|---|---|
| `cloud.excalidrawlib` | 19 | Generic cloud shapes |
| `cloud-design-patterns.excalidrawlib` | 24 | Cloud design patterns |
| `kubernetes-icons-set.excalidrawlib` | 19 | Kubernetes icons |
| `dev_ops.excalidrawlib` | 29 | DevOps tooling icons |

### `logos/` - technology logos
| File | Items | What |
|---|---|---|
| `technology-logos.excalidrawlib` | 18 | Technology/vendor logos |
| `it-logos.excalidrawlib` | 31 | IT product logos |

## Adding more libraries

Browse the full catalogue at <https://libraries.excalidraw.com> (from an unblocked
network), note the author/filename, then pull the raw file:
```bash
curl -sL "https://raw.githubusercontent.com/excalidraw/excalidraw-libraries/main/libraries/<author>/<name>.excalidrawlib" \
  -o <category>/<name>.excalidrawlib
```
AWS, Azure, Oracle Cloud, VMware, ArchiMate, UML and more are all available there.

## Attribution & license

Each `.excalidrawlib` is authored by its original creator and distributed under the
terms in the upstream repo (predominantly MIT). Source of truth:
<https://github.com/excalidraw/excalidraw-libraries>. This repo is only a convenience
mirror for use behind a restrictive proxy.
