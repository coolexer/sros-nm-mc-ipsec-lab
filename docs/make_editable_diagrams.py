"""Build a native, uncompressed draw.io workbook from this repository's SVG shapes.

This is intentionally limited to the SVG elements used by the lab generators.
Unknown elements/commands fail rather than silently becoming flattened images.
"""
from pathlib import Path
from collections import Counter
import re
import xml.etree.ElementTree as ET

DOCS = Path(__file__).resolve().parent
OUTPUT = DOCS/'lab-diagrams.drawio'
LAYERS = ('Frames', 'Physical links', 'Devices', 'Traffic and fault markers', 'Notes')


def number(value):
    return f'{float(value):.4f}'.rstrip('0').rstrip('.') if float(value) else '0'


def geometry(parent, bounds, **extra):
    x, y, width, height = bounds
    return ET.SubElement(parent, 'mxGeometry', x=number(x), y=number(y),
                         width=number(width), height=number(height), **extra, **{'as': 'geometry'})


def path_parts(data):
    tokens = re.findall(r'[A-Za-z]|-?\d+(?:\.\d+)?', data)
    parts, points, command = [], [], None
    x = y = 0.0
    curved = False
    while tokens:
        if tokens[0].isalpha():
            command = tokens.pop(0)
        if command in ('Z', 'z'):
            parts.append((points, curved, True))
            points = []
            command = None
            continue
        if command not in ('M', 'L', 'H', 'h', 'C', 'Q'):
            raise ValueError(f'Unsupported path command: {command}')
        count = {'M': 2, 'L': 2, 'H': 1, 'h': 1, 'C': 6, 'Q': 4}[command]
        values = [float(tokens.pop(0)) for _ in range(count)]
        if command == 'M' and points:
            parts.append((points, curved, False))
            points, curved = [], False
        if command in ('H', 'h'):
            x = values[0] if command == 'H' else x+values[0]
            points.append((x, y))
        else:
            points.extend(zip(values[::2], values[1::2]))
            x, y = points[-1]
        curved |= command in ('C', 'Q')
        if command == 'M':
            command = 'L'
    if points:
        parts.append((points, curved, False))
    return parts


def flatten(node, inherited=None):
    tag = node.tag.rsplit('}', 1)[-1]
    if tag == 'defs':
        return
    if 'transform' in node.attrib:
        raise ValueError('SVG transforms are outside the lab generator format')
    attrs = dict(inherited or {}, **node.attrib)
    if tag in ('svg', 'g'):
        for child in node:
            yield from flatten(child, attrs)
    elif tag in ('rect', 'text', 'circle', 'line', 'polyline', 'path'):
        yield tag, attrs, ''.join(node.itertext())
    else:
        raise ValueError(f'Unsupported SVG element: {tag}')


def build_page(svg, page_name):
    source = ET.parse(svg).getroot()
    _, _, width, height = map(float, source.attrib['viewBox'].split())
    model = ET.Element('mxGraphModel', dx=number(width), dy=number(height), grid='0', gridSize='10',
                       guides='1', tooltips='1', connect='1', arrows='1', fold='1', page='1',
                       pageScale='1', pageWidth=number(width), pageHeight=number(height), math='0', shadow='0')
    root = ET.SubElement(model, 'root')
    ET.SubElement(root, 'mxCell', id='0')
    for i, layer in enumerate(LAYERS, 1):
        ET.SubElement(root, 'mxCell', id=str(i), value=layer, parent='0')
    items = list(flatten(source))
    containers, shapes, edges = [], [], []

    def cell(style, bounds, value='', parent='3', edge=False, **extra):
        item = ET.Element('mxCell', id=f'c{len(shapes)+len(edges)}', value=value,
                          style=style, parent=parent, **({'edge': '1'} if edge else {'vertex': '1'}), **extra)
        geometry(item, bounds, **({'relative': '1'} if edge else {}))
        (edges if edge else shapes).append(item)
        return item

    def paint(attrs):
        style = f"fillColor={attrs.get('fill', 'black')};strokeColor={attrs.get('stroke', 'none')};strokeWidth={attrs.get('stroke-width', '1')};"
        if 'stroke-dasharray' in attrs:
            style += 'dashed=1;dashPattern=4 3;'
        return style

    # Create real container vertices first; labels and component cards move with them.
    for index, (tag, a, _) in enumerate(items):
        if tag == 'path':
            for points, _, closed in path_parts(a['d']):
                if closed:
                    # The source's only filled, closed non-marker path is the core cloud.
                    x, y = min(p[0] for p in points), min(p[1] for p in points)
                    bounds = (x, y, max(p[0] for p in points)-x, max(p[1] for p in points)-y)
                    item = cell('shape=cloud;'+paint(a)+'container=1;collapsible=0;', bounds)
                    containers.append((item, bounds))
        if tag != 'rect':
            continue
        bounds = tuple(float(a.get(key, 0)) for key in ('x', 'y', 'width', 'height'))
        x, y, w, h = bounds
        if x == y == 0 and w == width and h == height:
            continue  # White page background is supplied by the editor.
        style = 'rounded=1;absoluteArcSize=1;arcSize='+a.get('rx', '0')+';' if 'rx' in a else 'rounded=0;'
        candidate = 70 <= w <= 900 and 40 <= h <= 400
        item = cell(style+paint(a)+'container=1;collapsible=0;recursiveResize=0;', bounds,
                    parent='3' if candidate else '1')
        item.set('svgElement', str(index))
        if candidate:
            containers.append((item, bounds))

    def enclosing(bounds, skip=None):
        x, y, w, h = bounds
        candidates = [(bw*bh, item, (bx, by, bw, bh)) for item, (bx, by, bw, bh) in containers
                      if item is not skip and bx <= x and by <= y and x+w <= bx+bw and y+h <= by+bh
                      and (w == h == 0 or bw*bh > w*h)]
        return min(candidates, key=lambda row: row[0])[1:] if candidates else None

    def reparent(item, absolute_bounds):
        found = enclosing(absolute_bounds, item)
        if found:
            parent, (px, py, _, _) = found
            item.set('parent', parent.get('id'))
            geo = item.find('mxGeometry')
            geo.set('x', number(absolute_bounds[0]-px))
            geo.set('y', number(absolute_bounds[1]-py))

    for item, bounds in containers:
        reparent(item, bounds)

    def add_edge(points, attrs, curved=False, decoration=False):
        if len(points) < 2:
            return
        stroke = attrs.get('stroke', 'black')
        if stroke.lower() in ('white', '#ffffff') and float(attrs.get('stroke-width', 0)) >= 8:
            return  # A white SVG halo is decoration, not an additional network link.
        arrow = 'marker-end' in attrs
        traffic = arrow or stroke.lower() in ('#c62828', '#c42b32')
        style = ('edgeStyle=none;rounded=0;html=0;endArrow='+('block' if arrow else 'none')+
                 ';startArrow=none;endFill=1;endSize=8;strokeColor='+stroke+
                 ';strokeWidth='+attrs.get('stroke-width', '1')+';')
        if 'stroke-dasharray' in attrs:
            style += 'dashed=1;dashPattern=4 3;'
        if curved:
            style += 'curved=1;'
        item = cell(style, (0, 0, 0, 0), parent='4' if traffic else '2', edge=True)
        geo = item.find('mxGeometry')
        for name, point in [('source', points[0]), ('target', points[-1])]:
            ET.SubElement(geo, 'mxPoint', x=number(point[0]), y=number(point[1]), **{'as': name+'Point'})
            candidates = []
            if not decoration:
                for vertex, (x, y, w, h) in containers:
                    px, py = point
                    if x-12 <= px <= x+w+12 and y-12 <= py <= y+h+12:
                        distance = min(abs(px-x), abs(px-x-w), abs(py-y), abs(py-y-h))
                        if distance <= (40 if vertex.get('style', '').startswith('shape=cloud;') else 12):
                            candidates.append((distance, w*h, vertex, (x, y, w, h)))
            if candidates:
                _, _, vertex, (x, y, w, h) = min(candidates, key=lambda row: row[:2])
                item.set(name, vertex.get('id'))
                prefix = 'exit' if name == 'source' else 'entry'
                # Fixed attachment points retain the published noncrossing corridors.
                style += f'{prefix}X={number((point[0]-x)/w)};{prefix}Y={number((point[1]-y)/h)};{prefix}Perimeter=0;'
        if len(points) > 2:
            array = ET.SubElement(geo, 'Array', **{'as': 'points'})
            for x, y in points[1:-1]:
                ET.SubElement(array, 'mxPoint', x=number(x), y=number(y))
        item.set('style', style)
        if decoration:
            low_x = min(x for x, _ in points)
            low_y = min(y for _, y in points)
            bounds = (low_x, low_y, max(x for x, _ in points)-low_x, max(y for _, y in points)-low_y)
            found = enclosing(bounds)
            if found:
                parent, (px, py, _, _) = found
                item.set('parent', parent.get('id'))
                for point in geo.iter('mxPoint'):
                    point.set('x', number(float(point.get('x'))-px))
                    point.set('y', number(float(point.get('y'))-py))

    for tag, a, text in items:
        if tag == 'text':
            x, y, size = float(a.get('x', 0)), float(a.get('y', 0)), float(a.get('font-size', 16))
            anchor = a.get('text-anchor', 'start')
            w, h = max(20, len(text)*size*0.7), size*1.2
            # Text remains unwrapped/visible; oversized selection boxes must not add export pages.
            available = width-x-5 if anchor == 'start' else x-5 if anchor == 'end' else 2*min(x, width-x)-10
            w = min(w, max(1, available))
            left = x-w/2 if anchor == 'middle' else x-w if anchor == 'end' else x
            style = ('text;html=0;whiteSpace=nowrap;overflow=visible;spacing=0;verticalAlign=middle;'+
                     f"align={dict(start='left', middle='center', end='right')[anchor]};fontFamily=Arial;fontSize={number(size)};"+
                     f"fontColor={a.get('fill', 'black')};fontStyle={1 if float(a.get('font-weight', 400)) >= 600 else 0};")
            item = cell(style, (left, y-size*0.95, w, h), text, parent='5')
            found = enclosing((x, y-size*0.35, 0, 0))
            if found:
                parent, (px, py, _, _) = found
                item.set('parent', parent.get('id'))
                geo = item.find('mxGeometry')
                geo.set('x', number(left-px))
                geo.set('y', number(y-size*0.95-py))
        elif tag == 'circle':
            x, y, radius = (float(a[k]) for k in ('cx', 'cy', 'r'))
            bounds = (x-radius, y-radius, radius*2, radius*2)
            item = cell('ellipse;'+paint(a), bounds, parent='4')
            reparent(item, bounds)
        elif tag == 'line':
            add_edge([(float(a['x1']), float(a['y1'])), (float(a['x2']), float(a['y2']))], a)
        elif tag == 'polyline':
            add_edge([tuple(map(float, point.split(','))) for point in a['points'].split()], a)
        elif tag == 'path':
            for points, curved, closed in path_parts(a['d']):
                if closed:
                    continue  # Already created as a device container above.
                else:
                    add_edge(points, a, curved, decoration='Q' in a['d'])

    # Parents precede their children, and shapes precede connectors in the XML model.
    pending = shapes+edges
    known = {str(i) for i in range(6)}
    while pending:
        ready = [item for item in pending if item.get('parent') in known]
        if not ready:
            raise ValueError('Cyclic diagram parent relationship')
        for item in ready:
            root.append(item)
            known.add(item.get('id'))
            pending.remove(item)
    cells = list(root)
    assert len({item.get('id') for item in cells}) == len(cells)
    assert Counter(text for tag, _, text in items if tag == 'text') == Counter(
        item.get('value') for item in shapes if item.get('style', '').startswith('text;'))
    assert all(item.get(name) in known for item in edges for name in ('source', 'target') if name in item.attrib)
    assert all('image=' not in item.get('style', '') for item in cells)
    assert any(item.get('source') and item.get('target') for item in edges), page_name
    return ET.Element('diagram', id=page_name.replace(' ', '-'), name=page_name), model


def main():
    workbook = ET.Element('mxfile', host='app.diagrams.net', agent='Lab diagram generator',
                          type='device', compressed='false')
    pages = [(DOCS/'topology.svg', 'Overview - compact'),
             (DOCS/'topology-dual-iom.svg', 'Overview - dual IOM'),
             (DOCS/'redundancy-logic.svg', 'Redundancy logic')]
    cases = [p.stem.removesuffix('-paths') for p in (DOCS/'topology-scenarios').glob('*.svg')]
    def case_order(case):
        match = re.fullmatch(r'T(\d+)(.*)', case)
        return int(match[1]), match[2]
    for case in sorted(cases, key=case_order):
        pages += [(DOCS/'topology-scenarios'/f'{case}-paths.svg', f'{case} - topology'),
                  (DOCS/'scenarios'/f'{case}.svg', f'{case} - processing')]
    assert len(pages) == 61 and len({name for _, name in pages}) == 61
    for source, name in pages:
        diagram, model = build_page(source, name)
        diagram.append(model)
        workbook.append(diagram)
    ET.indent(workbook)
    OUTPUT.write_text(ET.tostring(workbook, encoding='unicode')+'\n', encoding='utf-8', newline='\n')
    print(f'Wrote {OUTPUT.name}: {len(pages)} pages, native shapes and connectors.')


if __name__ == '__main__':
    main()
