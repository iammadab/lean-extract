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
