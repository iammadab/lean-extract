import json
import subprocess
import sys

def get_contributors(file_path, start_line, end_line):
    try:
        blame_output = subprocess.check_output(
            ['git', 'blame', '--porcelain', '-L', f'{start_line},{end_line}', file_path],
            text=True, cwd='.'  # Assume cwd is Git root
        )
        contributors = {}
        current_hash = None
        current_author = None
        current_email = None
        lines = blame_output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if len(line) > 40 and line[40] == ' ' and line[:40].isalnum():  # Commit hash line
                if current_author and current_hash:
                    if current_author not in contributors:
                        contributors[current_author] = {"email": current_email, "hashes": set()}
                    contributors[current_author]["hashes"].add(current_hash)
                current_hash = line.split()[0]
            elif line.startswith('author '):
                current_author = line[7:].strip()
            elif line.startswith('author-mail '):
                current_email = line[12:].strip().strip('<>').strip()  # Remove <> if present
            elif line.startswith('\t'):  # Content line, end of header
                pass
            i += 1
        # Add the last one
        if current_author and current_hash:
            if current_author not in contributors:
                contributors[current_author] = {"email": current_email, "hashes": set()}
            contributors[current_author]["hashes"].add(current_hash)
        # Convert to list of dicts
        result = []
        for author, data in contributors.items():
            result.append({
                "name": author,
                "email": data["email"],
                "commit_hashes": list(data["hashes"])
            })
        return result
    except Exception as e:
        return [{"error": str(e)}]

def generate_graph(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    # Embed JSON data as JS variable
    json_data_str = json.dumps(data)
    # Generate HTML content with enhanced styling and tree-like layout
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dependency Graph</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            margin: 0;
            display: flex;
            font-family: 'Arial', sans-serif; /* Sans-serif font for the whole page */
            background-color: #f4f4f9;
            color: #333;
        }}
        #graph {{
            width: 70%;
            height: 100vh;
            border: 1px solid #ddd;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: width 0.3s;
        }}
        #graph.full {{
            width: 100%;
        }}
        #details {{
            width: 30%;
            height: 100vh;
            padding: 20px;
            overflow-y: auto;
            background-color: #ffffff;
            border-left: 1px solid #ddd;
            font-family: 'Helvetica', sans-serif; /* Specific sans-serif for side pane */
            line-height: 1.6;
            box-shadow: -2px 0 4px rgba(0,0,0,0.05);
            position: relative;
            transition: width 0.3s;
        }}
        #details.hidden {{
            width: 0;
            padding: 0;
            overflow: hidden;
        }}
        #close-details {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #e74c3c;
            color: white;
            border: none;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            cursor: pointer;
            font-weight: bold;
        }}
        h3 {{
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }}
        h4 {{
            color: #34495e;
            margin-bottom: 10px;
        }}
        ul {{
            list-style-type: none;
            padding: 0;
        }}
        li {{
            margin-bottom: 15px;
            background: #f9f9f9;
            padding: 10px;
            border-radius: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }}
        strong {{ color: #2980b9; }}
        p {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <div id="graph"></div>
    <div id="details">
        <button id="close-details">X</button>
        <h3>Node Details</h3>
        <p>Click a node to view details.</p>
    </div>
    <script>
        const data = {json_data_str};
        // Prepare nodes and edges for Vis.js
        const nodes = new vis.DataSet(data.map(item => ({{
            id: item.name,
            label: `${{item.name.split('.').pop()}}\\n(${{item.constCategory}})`,
            title: item.constType, // Hover tooltip for type
            shape: 'box',
            color: {{ background: '#add8e6', border: '#4682b4' }},
            font: {{ face: 'Arial', color: '#2c3e50' }},
            margin: 10
        }})));
        const edges = [];
        data.forEach(item => {{
            item.references.forEach(ref => {{
                if (data.some(n => n.name === ref)) {{ // Only internal
                    edges.push({{
                        from: item.name,
                        to: ref,
                        color: {{ color: '#7f8c8d' }},
                        smooth: {{ type: 'curvedCW' }} // Slight curve for tree aesthetic
                    }});
                }}
            }});
        }});
        const container = document.getElementById('graph');
        const options = {{
            layout: {{
                hierarchical: {{
                    direction: 'UD', // Up-Down for theorem at top
                    sortMethod: 'directed', // Directed for dependency flow
                    shakeTowards: 'roots', // Tree-like, roots at top
                    levelSeparation: 150, // Spacing for tree feel
                    nodeSpacing: 200
                }}
            }},
            physics: {{ enabled: false }},
            edges: {{ arrows: 'to' }}
        }};
        const network = new vis.Network(container, {{ nodes, edges: new vis.DataSet(edges) }}, options);
        const detailsPane = document.getElementById('details');
        const graphDiv = document.getElementById('graph');
        document.getElementById('close-details').addEventListener('click', function() {{
            detailsPane.classList.add('hidden');
            graphDiv.classList.add('full');
        }});
        // Click event to show details
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                detailsPane.classList.remove('hidden');
                graphDiv.classList.remove('full');
                const nodeId = params.nodes[0];
                const node = data.find(item => item.name === nodeId);
                if (node) {{
                    let html = `<button id="close-details">X</button><h3>${{node.name}} (${{node.constCategory}})</h3>`;
                    html += `<p><strong>Type:</strong> ${{node.constType}}</p>`;
                    html += `<p><strong>File:</strong> ${{node.file}} (Lines ${{node.startLine}}-${{node.endLine}})</p>`;
                    html += '<h4>Contributors:</h4><ul>';
                    node.contributors.forEach(c => {{
                        html += `<li><strong>${{c.name}}</strong> &lt;${{c.email}}&gt;<br>Commits: ${{c.commit_hashes.join(', ')}}</li>`;
                    }});
                    html += '</ul>';
                    detailsPane.innerHTML = html;
                    // Re-add event listener since HTML was overwritten
                    document.getElementById('close-details').addEventListener('click', function() {{
                        detailsPane.classList.add('hidden');
                        graphDiv.classList.add('full');
                    }});
                }}
            }}
        }});
    </script>
</body>
</html>
    """.strip()
    # Write to visualization.html
    with open('visualization.html', 'w') as f:
        f.write(html_content)
    print("Interactive visualization saved to visualization.html")
    print("Open visualization.html in a web browser to view and interact with the graph.")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python contributors.py input.json")
        sys.exit(1)
    contrib_path = "contributors.json"
    with open(sys.argv[1], 'r') as f:
        data = json.load(f)
    for node in data:
        if 'file' in node and 'startLine' in node and 'endLine' in node:
            contributors = get_contributors(node['file'], node['startLine'], node['endLine'])
            node['contributors'] = contributors
    with open(contrib_path, 'w') as f:
        json.dump(data, f, indent=2)
    print("Attribution complete; output in", contrib_path)
    # generate visualization
    generate_graph(contrib_path)
