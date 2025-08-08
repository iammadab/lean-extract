# lean-extract

**lean-extract** is a set of scripts for extracting the **dependency graph** of a given theorem in Lean and enriching it with **Git history** metadata.

## Features
- Extracts all dependencies for a specified theorem, up to a configurable depth.
- Outputs the graph in JSON for easy visualization or further processing.
- Integrates with Git to attribute each node to its author and timestamp.

## Use Cases
- Visualize how a theorem depends on other results.
- Analyze contribution patterns in a Lean project.
- Identify foundational lemmas and their authors.

## Sample Output
<img width="1547" height="768" alt="image" src="https://github.com/user-attachments/assets/b71fd41a-d895-4b63-96fd-c92f038f2328" />

<img width="1766" height="810" alt="image" src="https://github.com/user-attachments/assets/18c60f69-174f-4630-bedb-99bae8d6dcff" />
