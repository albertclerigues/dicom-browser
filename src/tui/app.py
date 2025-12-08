import asyncio

from pydicom.dataset import Dataset
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Input, Static, Tree
from textual.widgets.tree import TreeNode

from src.dicom.loader import iter_dataset, load_dicom

TAG_COLOR = "#0F8B8D"
NAME_COLOR = "#1A73A3"
VR_COLOR = "#005DAA"
VALUE_COLOR = "#F5F7FA"


class dcmbrowser(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("left", "collapse_node", "Collapse"),
        ("right", "expand_node", "Expand"),
        ("ctrl+e", "expand_all", "Expand All"),
        ("ctrl+w", "collapse_all", "Collapse All"),
        ("ctrl+f", "toggle_search", "Toggle Search"),
    ]

    def __init__(self, dicom_path: str):
        super().__init__()
        self.dicom_path = dicom_path
        self.node_data = {}  # Maps node.id to (tag, name, value_str)
        self.all_nodes = []  # All leaf and branch nodes for searching
        self.search_timer = None  # For debouncing search input
        self.search_visible = False  # Track search box visibility

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(
            placeholder="Search tags (name or value)...",
            id="search-input",
            classes="hidden",
        )
        yield Static("", id="status-message", classes="hidden")
        yield Tree("DICOM Root")
        yield Footer()

    def on_mount(self) -> None:
        header = self.query_one(Header)
        header.tall = False
        header.icon = "📋"

        tree = self.query_one(Tree)
        tree.root.expand()

        try:
            ds = load_dicom(self.dicom_path)
            # Set root label to filename
            tree.root.label = f"{self.dicom_path}"
            self.populate_tree(tree.root, ds)
        except Exception as e:
            tree.root.add(f"[bold red]Error loading file:[/bold red] {e}")

    def _on_key(self, event) -> None:
        """Handle key events at app level to intercept Ctrl+F."""
        if event.key == "ctrl+f":
            self.action_toggle_search()
            event.prevent_default()

    def populate_tree(self, node: TreeNode, dataset: Dataset) -> None:
        for tag, name, vr, value_str, raw_value in iter_dataset(dataset):
            # Format the label with fixed-width columns
            # Tag: 13 chars, Name: 40 chars, VR: 4 chars, Value: remaining
            tag_col = f"[bold {TAG_COLOR}]{tag:<13}[/]"
            name_col = f"[bold {NAME_COLOR}]{name:<40}[/]"
            vr_col = f"[{VR_COLOR}]{vr:<4}[/]"
            value_col = f"[{VALUE_COLOR}]{value_str}[/]"

            label = f"{tag_col} {name_col} {vr_col} {value_col}"

            if vr == "SQ":
                child = node.add(label, expand=False)
                # Store data for searching
                self.node_data[child.id] = (tag, name, value_str)
                self.all_nodes.append(child)
                # Handle Sequence
                for i, item in enumerate(raw_value):
                    item_node = child.add(f"[bold]Item {i+1}[/]", expand=False)
                    self.populate_tree(item_node, item)
            else:
                leaf = node.add_leaf(label)
                # Store data for searching
                self.node_data[leaf.id] = (tag, name, value_str)
                self.all_nodes.append(leaf)

    def populate_tree_filtered(
        self,
        node: TreeNode,
        dataset: Dataset,
        nodes_to_show: set,
        old_node_data: dict,
        query: str,
    ) -> None:
        """Populate tree with only nodes that match the search query."""
        for tag, name, vr, value_str, raw_value in iter_dataset(dataset):
            # Check if this node matches the search
            is_match = query in name.lower() or query in value_str.lower()

            # Format the label with fixed-width columns
            tag_col = f"[bold {TAG_COLOR}]{tag:<13}[/]"

            # Highlight matches in name
            if query in name.lower():
                idx = name.lower().index(query)
                name_highlighted = (
                    name[:idx]
                    + f"[#0D1117 on {VR_COLOR}]{name[idx:idx+len(query)]}[/]"
                    + name[idx + len(query) :]
                )
                name_col = f"[bold]{name_highlighted:<40}[/]"
            else:
                name_col = f"[bold]{name:<40}[/]"

            vr_col = f"[#0F8B8D]{vr:<4}[/]"

            # Highlight matches in value
            if query in value_str.lower():
                idx = value_str.lower().index(query)
                value_highlighted = (
                    value_str[:idx]
                    + f"[#0D1117 on {VR_COLOR}]{value_str[idx:idx+len(query)]}[/]"
                    + value_str[idx + len(query) :]
                )
                value_col = f"[{VALUE_COLOR}]{value_highlighted}[/]"
            else:
                value_col = f"[{VALUE_COLOR}]{value_str}[/]"

            label = f"{tag_col} {name_col} {vr_col} {value_col}"

            if vr == "SQ":
                # For sequences, check if any child matches
                has_matching_child = self.sequence_has_match(raw_value, query)

                if is_match or has_matching_child:
                    child = node.add(label, expand=False)
                    self.node_data[child.id] = (tag, name, value_str)
                    self.all_nodes.append(child)
                    # Handle Sequence items
                    for i, item in enumerate(raw_value):
                        item_node = child.add(f"[bold]Item {i+1}[/]", expand=False)
                        self.populate_tree_filtered(
                            item_node, item, nodes_to_show, old_node_data, query
                        )
            else:
                if is_match:
                    leaf = node.add_leaf(label)
                    self.node_data[leaf.id] = (tag, name, value_str)
                    self.all_nodes.append(leaf)

    def sequence_has_match(self, sequence, query: str) -> bool:
        """Check if any item in a sequence matches the search query."""
        for item in sequence:
            for tag, name, vr, value_str, raw_value in iter_dataset(item):
                if query in name.lower() or query in value_str.lower():
                    return True
                if vr == "SQ" and self.sequence_has_match(raw_value, query):
                    return True
        return False

    def action_expand_node(self) -> None:
        """Expand the currently selected tree node."""
        tree = self.query_one(Tree)
        if tree.cursor_node and not tree.cursor_node.is_expanded:
            tree.cursor_node.expand()

    def action_collapse_node(self) -> None:
        """Collapse the currently selected tree node."""
        tree = self.query_one(Tree)
        if tree.cursor_node and tree.cursor_node.is_expanded:
            tree.cursor_node.collapse()

    def action_expand_all(self) -> None:
        """Expand all nodes in the tree."""
        tree = self.query_one(Tree)
        for node in self.all_nodes:
            if not node.is_expanded and node.allow_expand:
                node.expand()
        tree.root.expand_all()
        self.update_status("All nodes expanded")

    def action_collapse_all(self) -> None:
        """Collapse all nodes in the tree."""
        tree = self.query_one(Tree)
        tree.root.collapse_all()
        self.update_status("All nodes collapsed")

    def action_toggle_search(self) -> None:
        """Toggle the visibility of the search input."""
        search_input = self.query_one("#search-input", Input)
        status_message = self.query_one("#status-message", Static)
        self.search_visible = not self.search_visible

        if self.search_visible:
            search_input.remove_class("hidden")
            status_message.remove_class("hidden")
            search_input.focus()
        else:
            search_input.add_class("hidden")
            status_message.add_class("hidden")
            # Clear search when hiding
            search_input.value = ""
            # Restore original tree
            tree = self.query_one(Tree)
            tree.clear()
            tree.root.expand()
            ds = load_dicom(self.dicom_path)
            tree.root.label = f"{self.dicom_path}"
            self.node_data.clear()
            self.all_nodes.clear()
            self.populate_tree(tree.root, ds)
            tree.root.collapse_all()
            tree.root.expand()
            self.update_status("")

    def update_status(self, message: str) -> None:
        """Update the status message display."""
        status = self.query_one("#status-message", Static)
        status.update(f"[bold #1A73A3]{message}[/]")

    @work(exclusive=True)
    async def perform_search(self, query: str) -> None:
        """Perform fuzzy search on tree nodes with debouncing."""
        # Debounce: wait 300ms
        await asyncio.sleep(0.3)

        tree = self.query_one(Tree)
        query_lower = query.lower().strip()

        if not query_lower:
            # Empty search: restore original tree, collapse all
            tree.clear()
            tree.root.expand()
            ds = load_dicom(self.dicom_path)
            tree.root.label = f"{self.dicom_path}"
            self.node_data.clear()
            self.all_nodes.clear()
            self.populate_tree(tree.root, ds)
            tree.root.collapse_all()
            tree.root.expand()
            self.update_status("")
            return

        # Find matching nodes
        matching_nodes = []
        matching_data = []
        for node in self.all_nodes:
            if node.id in self.node_data:
                tag, name, value_str = self.node_data[node.id]
                # Fuzzy search: check if query appears in name or value
                if query_lower in name.lower() or query_lower in value_str.lower():
                    matching_nodes.append(node)
                    matching_data.append((tag, name, value_str))

        match_count = len(matching_nodes)

        if match_count == 0:
            self.update_status("[bold #005DAA]No matches found[/]")
            # Rebuild tree with no nodes
            tree.clear()
            tree.root.expand()
            tree.root.label = f"{self.dicom_path}"
        else:
            self.update_status(f"[bold #1A73A3]{match_count} match(es) found[/]")

            # Collect all nodes to show (matches + their ancestors)
            nodes_to_show = set(matching_nodes)
            for node in matching_nodes:
                current = node.parent
                while current and current != tree.root:
                    nodes_to_show.add(current)
                    current = current.parent

            # Rebuild tree with only matching nodes
            tree.clear()
            tree.root.expand()
            ds = load_dicom(self.dicom_path)
            tree.root.label = f"{self.dicom_path}"
            old_node_data = self.node_data.copy()
            self.node_data.clear()
            self.all_nodes.clear()
            self.populate_tree_filtered(
                tree.root, ds, nodes_to_show, old_node_data, query_lower
            )

            # Expand all nodes to show matches
            tree.root.expand_all()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes with debouncing."""
        if event.input.id == "search-input":
            self.perform_search(event.value)
