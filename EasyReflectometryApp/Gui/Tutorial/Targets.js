.pragma library

// Finds the controls a tutorial points at: items with an `objectName` of the form
// '<page>.<control>' or 'appbar.<page>Tab' (MD/INTERACTIVE_TUTORIALS_DESIGN.md, section 5.5).
// Each name is given to exactly one item (tests/test_tutorials.py checks the QML sources).

const PAGES = ['home', 'project', 'sample', 'experiment', 'analysis', 'summary']

const _cache = {}

// The item named `name` under `root` (the window's content item), or null.
function find(root, name) {
    const cached = _cache[name]
    if (cached && cached.objectName === name) {
        return cached
    }
    const item = _search(root, name)
    if (item) {
        _cache[name] = item
    } else {
        delete _cache[name]
    }
    return item
}

function _search(item, name) {
    if (item.objectName === name) {
        return item
    }
    const children = item.children
    for (let i = 0; i < children.length; ++i) {
        const found = _search(children[i], name)
        if (found) {
            return found
        }
    }
    return null
}

// The collapsed sidebar group (EaElements.GroupBox) that hides the item, or null. Groups
// start collapsed, so a step's control is often inside one.
function collapsedGroup(item) {
    for (let ancestor = item.parent; ancestor; ancestor = ancestor.parent) {
        if (ancestor.collapsible === true && ancestor.collapsed === true) {
            return ancestor
        }
    }
    return null
}

// Whether the user can see the item: visible, and not clipped away by a scrolled or
// switched container (the sidebar's tabs and scroll area clip their content).
function isShown(item) {
    if (!item || !item.visible || item.width <= 0 || item.height <= 0) {
        return false
    }
    for (let ancestor = item.parent; ancestor; ancestor = ancestor.parent) {
        if (ancestor.clip) {
            const r = item.mapToItem(ancestor, 0, 0, item.width, item.height)
            if (r.x + r.width <= 0 || r.y + r.height <= 0 || r.x >= ancestor.width || r.y >= ancestor.height) {
                return false
            }
        }
    }
    return true
}
