async function fetchAndRenderTree() {
    try {
        const response = await fetch("/api/tree");
        const treeData = await response.json();
        renderTree(treeData);
    } catch (error) {
        console.error("Error fetching tree data:", error);
    }
}

async function fetchAndRenderDouble() {
    try{
        const response = await fetch("/api/double");
        console.log("Fetching double tree data");
        const doubleTree = await response.json();
        renderDoubleTree(doubleTree['bigTree'], doubleTree['smallTree']);
    } catch (error) {
        console.error("Error fetching tree data:", error);
    }
}

async function fetchAndRenderThree(){
    try{
        const response = await fetch("/api/three");
        console.log("Fetching 3 tree data");
        const threeTree = await response.json();
        renderThreeTree(threeTree);
    } catch (error) {
        console.error("Error fetching 3 tree:", error);
    }
}

async function fetchAndRenderQuad(){
    try{
        const response = await fetch("/api/quad");
        console.log("Fetching quad tree data");
        const quadTree = await response.json();
        renderQuadTree(quadTree);
    } catch (error) {
        console.error("Error fetching 4 tree:", error);
    }
}

async function fetchAndRenderFive() {
    try{
        const response = await fetch("/api/five");
        console.log("Fetching five tree data");
        const fiveTree = await response.json();
        renderFiveTree(fiveTree);
    } catch (error) {
        console.error("Error fetching five tree:", error);
    }
}

// This is for rendering a single tree
// document.addEventListener("DOMContentLoaded", fetchAndRenderTree);

// This is for rendering two trees
// document.addEventListener("DOMContentLoaded", fetchAndRenderDouble);

// This is for rendering three trees
document.addEventListener("DOMContentLoaded", fetchAndRenderThree);

// This is for rendering four trees
// document.addEventListener("DOMContentLoaded", fetchAndRenderQuad);

// This is for rendering five trees
// document.addEventListener("DOMContentLoaded", fetchAndRenderFive);


function renderTree(treeData) {
    // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.59; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const tree = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1.5) / a.depth);

    // Sort the tree and apply the layout.
    const root = tree(d3.hierarchy(treeData)
        .sort((a, b) => d3.ascending(a.data.name, b.data.name)));

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(root.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y));

    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(root.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        // .attr("fill", d => {
        //     if (!d.children) return "#8ecfc9";// 叶子节点
        //     else if (d.data.name === root.data.name) return "#beb8dc"; // 根节点
        //     else return "#82b0d2";// 中间节点
        // })
        // 根据 d.data.is_leaf 来设置颜色
        .attr("fill", d => {
            // 若是叶子节点
            if (d.data.is_leaf) {
                return "#8ecfc9"; // 叶子节点
            }
            // 若是根节点（判断方法可根据名称或 depth 来判断，这里沿用你原始的比较方式）
            else if (d.data.name === root.data.name) {
                return "#beb8dc"; // 根节点
            }
            // 其他节点
            else {
                return "#82b0d2"; // 中间节点
            }
        })
        .attr("r", 3)
        // 添加鼠标悬停显示节点名称的事件
        .on("mouseover", function(event, d) { // 鼠标悬停事件
            const tooltip = d3.select("body").append("div") // 创建 tooltip 元素
                .attr("class", "tooltip")
                .style("position", "absolute")
                .style("background", "rgba(0,0,0,0.7)")
                .style("color", "white")
                .style("border-radius", "5px")
                .style("padding", "5px")
                .style("pointer-events", "none")
                .text(d.data.name); // 显示节点名称
            tooltip.style("left", (event.pageX + 5) + "px") // 设置 tooltip 位置
                .style("top", (event.pageY + 5) + "px");
        })
        .on("mouseout", function(d) { // 鼠标移开事件
            d3.select(".tooltip").remove(); // 移除 tooltip
        });


    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        .text(d => {
            if (!d.children) {
                // 如果是叶子节点
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
        })  // 为每个节点分配序号，从 1 开始
        .attr("font-size", "8px")  // 设置字体大小
        .attr("fill", "black");  // 设置字体颜色


    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    sortedEntries.forEach(([substance, idx]) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${idx}</td><td>${substance}</td>`;
        tbody.appendChild(row);
    });
}

function renderDoubleTree(bigTreeData, smallTreeData){
    // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.5; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const treeLayout = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1) / a.depth);

    // Sort the tree and apply the layout.
    const bigTreeRoot = d3.hierarchy(bigTreeData);
    const smallTreeRoot = d3.hierarchy(smallTreeData);
    treeLayout(bigTreeRoot);

    // 初始化大树所有节点的isPathPoint属性为false
    bigTreeRoot.each(d => d.isPathPoint = false);

    // 层次遍历获取小树的节点集合
    const smallTreeLevels = getNodesByLevel(smallTreeRoot);

    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths(bigTreeRoot, smallTreeLevels);

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(bigTreeRoot.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y));

    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(bigTreeRoot.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        .attr("fill", d => {
            if (!d.children) return "#8ecfc9";// 叶子节点
            else if (d.data.name === bigTreeRoot.data.name) return "#beb8dc"; // 根节点
            else return "#82b0d2";// 中间节点
        })
        .attr("class", d => d.isPathPoint ? "highlight" : "normal");

    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        .text(d => {
            if (!d.children) {
                // 如果是叶子节点
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
        })  // 为每个节点分配序号，从 1 开始
        .attr("font-size", "10px")  // 设置字体大小
        .attr("fill", "black");  // 设置字体颜色

    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    const datasPerRow = 3;
    let currentRow = document.createElement("tr");
    sortedEntries.forEach(([substance, idx]) => {
        const cell = document.createElement('td');
        cell.innerHTML = `<td>${idx}: ${substance}</td>`;
        currentRow.appendChild(cell);

        if(idx % datasPerRow === 0) {
            tbody.appendChild(currentRow);
            currentRow = document.createElement("tr");
        }
    });

    // 下载按钮
    // 下载SVG图像
    // Add download button
    const button = document.getElementById("downloadBtn");
    button.innerText = "Download SVG";
    button.addEventListener("click", () => {
        const svgNode = svg.node();
        // 获取页面中所有的 <style> 标签内容
        const styleSheets = document.querySelectorAll("style");
        let styleContent = "";
        styleSheets.forEach(sheet => {
            styleContent += sheet.innerHTML;
        });

            // 创建一个 <style> 元素并添加到 SVG 的 <defs> 中
        const styleElement = document.createElementNS("http://www.w3.org/2000/svg", "style");
        styleElement.innerHTML = styleContent;
        svgNode.querySelector("defs")?.appendChild(styleElement) || svgNode.insertBefore(styleElement, svgNode.firstChild);

        const serializer = new XMLSerializer();
        const svgBlob = new Blob([serializer.serializeToString(svg.node())], {type: "image/svg+xml"});
        const url = URL.createObjectURL(svgBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "chart.svg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

function renderThreeTree(quadTree){
    const mainTree = quadTree['main'];
    const sonTree = quadTree['son'];
    const path1 = quadTree['path1'];
    // const path2 = quadTree['path2'];

    // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.5; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const treeLayout = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1) / a.depth);

    // Sort the tree and apply the layout.
    const mainTreeRoot = d3.hierarchy(mainTree);
    const sonTreeRoot = d3.hierarchy(sonTree);
    const path1TreeRoot = d3.hierarchy(path1);
    // const path2TreeRoot = d3.hierarchy(path2);
    treeLayout(mainTreeRoot);

    // 初始化大树所有节点的isPathPoint属性为false
    mainTreeRoot.each(d => d.isPathPoint = 0);

    // 0: main树
    // 1: 子树
    // 2: path1

    // 层次遍历获取小树的节点集合
    const sonTreeLevels = getNodesByLevel(sonTreeRoot);
    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths_v2(mainTreeRoot, sonTreeLevels, 1);

    // Bug-fixed: 25-1-5
    // -----------------------------------------***------------------------------------------
    // // 层次遍历获取小树的节点集合
    // const path1TreeLevels = getNodesByLevel(path1TreeRoot);
    // // 使用层序遍历匹配节点，并高亮路径
    // highlightPaths_v2(mainTreeRoot, path1TreeLevels, 2);
    //
    // // 层次遍历获取小树的节点集合
    // const path2TreeLevels = getNodesByLevel(path2TreeRoot);
    // // 使用层序遍历匹配节点，并高亮路径
    // highlightPaths_v2(mainTreeRoot, path2TreeLevels, 3);
    // -----------------------------------------***------------------------------------------
    // 层次遍历获取小树的节点集合
    const path1TreeLevels = getNodesByLevel(path1TreeRoot);
    // 使用层序遍历匹配节点，并高亮路径
    // value: 2, neg_value: 3, superior_value: 1
    highlightPaths_v3(mainTreeRoot, path1TreeLevels, value=2, neg_value=3, superior_value=1);

    // // 层次遍历获取小树的节点集合
    // const path2TreeLevels = getNodesByLevel(path2TreeRoot);
    // // 使用层序遍历匹配节点，并高亮路径
    // // value: 4, neg_value: 5, superior_value: 1
    // highlightPaths_v3(mainTreeRoot, path2TreeLevels, value=4, neg_value=5, superior_value=1);


    // 染色所有边
    // highlightLinks(mainTreeRoot.links());

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(mainTreeRoot.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y))
        .attr("class", d => {
            const source = d.source;
            const target = d.target;
            const num = target.isPathPoint;

            // Bug-fixed: 25-1-5
        // -----------------------------------------***------------------------------------------
        //     if(num === 1){
        //         return "highlightLinks";
        //     }
        //     else if (num === 2){
        //         return "path1Links";
        //     }
        //     else if (num === 3){
        //         return "path2Links";
        //     }
        //     else{
        //         return "normalLinks";
        //     }
        // });
                if(num === 1){
                return "highlightLinks";
            }
            else if (num === 2 || num === 3){
                return "path1Links";
            }
            // else if (num === 4 || num === 5){
            //     return "path2Links";
            // }
            else{
                return "normalLinks";
            }
        });
        // -----------------------------------------***------------------------------------------


    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(mainTreeRoot.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        // .attr("fill", d => {
        //     if (!d.children) return "#8ecfc9";// 叶子节点
        //     else if (d.data.name === mainTreeRoot.data.name) return "#beb8dc"; // 根节点
        //     else return "#82b0d2";// 中间节点
        // })
        .attr("fill", d => {
            // 根据 is_leaf 和节点类型设置不同的颜色
            if (d.data.is_leaf) return "#8ecfc9"; // 叶子节点
            else if (d.data.name === mainTreeRoot.data.name) return "#beb8dc"; // 根节点
            else return "#82b0d2"; // 中间节点
        })
        .attr("r", 3)
        // Bug-fixed: 25-1-5
        // -----------------------------------------***------------------------------------------
        .attr("class", d => {
            if(d.isPathPoint === 0){
                return "normal";
            }
            else if(d.isPathPoint === 1){
                return "highlight";
            }
            else if(d.isPathPoint === 2){
                return "path1_normal";
            }
            else if(d.isPathPoint === 3){
                return "path1_highlight";
            }
            // else if(d.isPathPoint === 4){
            //     return "path2_normal";
            // }
            // else if(d.isPathPoint === 5){
            //     return "path2_highlight";
            // }
            else{
                return "normal";
            }
        })

        // -----------------------------------------***------------------------------------------
        // 添加鼠标悬停显示节点名称的事件
        .on("mouseover", function(event, d) { // 鼠标悬停事件
            const tooltip = d3.select("body").append("div") // 创建 tooltip 元素
                .attr("class", "tooltip")
                .style("position", "absolute")
                .style("background", "rgba(0,0,0,0.7)")
                .style("color", "white")
                .style("border-radius", "5px")
                .style("padding", "5px")
                .style("pointer-events", "none")
                .text(d.data.name); // 显示节点名称
            tooltip.style("left", (event.pageX + 5) + "px") // 设置 tooltip 位置
                .style("top", (event.pageY + 5) + "px");
        })
        .on("mouseout", function(d) { // 鼠标移开事件
            d3.select(".tooltip").remove(); // 移除 tooltip
        });


    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        // .text(d => {
        //     if (!d.children) {
        //         // 如果是叶子节点
        //         let cur_idx = name_idx_dict[d.data.name];
        //         if (cur_idx !== undefined) {
        //             // 如果已有
        //             return cur_idx;
        //         } else {
        //             // 如果没有
        //             name_idx_dict[d.data.name] = idx;
        //             idx++;
        //             return idx - 1;
        //         }
        //     }
        // })  // 为每个节点分配序号，从 1 开始
        .text(d => {
            if (d.data.is_leaf) {  // 只为叶子节点分配标号
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
            return "";  // 非叶子节点不显示标号
        })  // 为叶子节点分配序号，从 1 开始
        .attr("font-size", "8px")  // 设置字体大小
        .attr("font-family", "Arial, sans-serif")  // 设置字体为 Arial
        .attr("fill", "black");  // 设置字体颜色

    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    const datasPerRow = 3;
    let currentRow = document.createElement("tr");
    sortedEntries.forEach(([substance, idx]) => {
        const cell = document.createElement('td');
        cell.innerHTML = `<td>${idx}: ${substance}</td>`;
        currentRow.appendChild(cell);

        if(idx % datasPerRow === 0) {
            tbody.appendChild(currentRow);
            currentRow = document.createElement("tr");
        }
    });

    // 下载按钮
    // 下载SVG图像
    // Add download button
    const button = document.getElementById("downloadBtn");
    button.innerText = "Download SVG";
    button.addEventListener("click", () => {
        const svgNode = svg.node();
        // 获取页面中所有的 <style> 标签内容
        const styleSheets = document.querySelectorAll("style");
        let styleContent = "";
        styleSheets.forEach(sheet => {
            styleContent += sheet.innerHTML;
        });
        // 创建一个 <style> 元素并添加到 SVG 的 <defs> 中
        const styleElement = document.createElementNS("http://www.w3.org/2000/svg", "style");
        styleElement.innerHTML = styleContent;
        svgNode.querySelector("defs")?.appendChild(styleElement) || svgNode.insertBefore(styleElement, svgNode.firstChild);

        const serializer = new XMLSerializer();
        const svgBlob = new Blob([serializer.serializeToString(svg.node())], {type: "image/svg+xml"});
        const url = URL.createObjectURL(svgBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "chart.svg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    console.log("4 tree completed!");
}

function renderQuadTree(quadTree){
    const mainTree = quadTree['main'];
    const sonTree = quadTree['son'];
    const path1 = quadTree['path1'];
    const path2 = quadTree['path2'];

    // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.5; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const treeLayout = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1) / a.depth);

    // Sort the tree and apply the layout.
    const mainTreeRoot = d3.hierarchy(mainTree);
    const sonTreeRoot = d3.hierarchy(sonTree);
    const path1TreeRoot = d3.hierarchy(path1);
    const path2TreeRoot = d3.hierarchy(path2); /////
    treeLayout(mainTreeRoot);

    // 初始化大树所有节点的isPathPoint属性为false
    mainTreeRoot.each(d => d.isPathPoint = 0);

    // 0: main树
    // 1: 子树
    // 2: path1
    // 3: path2

    // 层次遍历获取小树的节点集合
    const sonTreeLevels = getNodesByLevel(sonTreeRoot);
    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths_v2(mainTreeRoot, sonTreeLevels, 1);

    // Bug-fixed: 25-1-5
    // -----------------------------------------***------------------------------------------
    // // 层次遍历获取小树的节点集合
    // const path1TreeLevels = getNodesByLevel(path1TreeRoot);
    // // 使用层序遍历匹配节点，并高亮路径
    // highlightPaths_v2(mainTreeRoot, path1TreeLevels, 2);
    //
    // // 层次遍历获取小树的节点集合
    // const path2TreeLevels = getNodesByLevel(path2TreeRoot);
    // // 使用层序遍历匹配节点，并高亮路径
    // highlightPaths_v2(mainTreeRoot, path2TreeLevels, 3);
    // -----------------------------------------***------------------------------------------
    // 层次遍历获取小树的节点集合
    const path1TreeLevels = getNodesByLevel(path1TreeRoot);
    // 使用层序遍历匹配节点，并高亮路径
    // value: 2, neg_value: 3, superior_value: 1
    highlightPaths_v3(mainTreeRoot, path1TreeLevels, value=2, neg_value=3, superior_value=1);

    // 层次遍历获取小树的节点集合
    const path2TreeLevels = getNodesByLevel(path2TreeRoot);
    // 使用层序遍历匹配节点，并高亮路径
    // value: 4, neg_value: 5, superior_value: 1
    highlightPaths_v3(mainTreeRoot, path2TreeLevels, value=4, neg_value=5, superior_value=1);


    // 染色所有边
    // highlightLinks(mainTreeRoot.links());

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(mainTreeRoot.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y))
        .attr("class", d => {
            const source = d.source;
            const target = d.target;
            const num = target.isPathPoint;

            // Bug-fixed: 25-1-5
        // -----------------------------------------***------------------------------------------
        //     if(num === 1){
        //         return "highlightLinks";
        //     }
        //     else if (num === 2){
        //         return "path1Links";
        //     }
        //     else if (num === 3){
        //         return "path2Links";
        //     }
        //     else{
        //         return "normalLinks";
        //     }
        // });
                if(num === 1){
                return "highlightLinks";
            }
            else if (num === 2 || num === 3){
                return "path1Links";
            }
            else if (num === 4 || num === 5){
                return "path2Links";
            }
            else{
                return "normalLinks";
            }
        });
        // -----------------------------------------***------------------------------------------


    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(mainTreeRoot.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        // .attr("fill", d => {
        //     if (!d.children) return "#8ecfc9";// 叶子节点
        //     else if (d.data.name === mainTreeRoot.data.name) return "#beb8dc"; // 根节点
        //     else return "#82b0d2";// 中间节点
        // })
        .attr("fill", d => {
            // 根据 is_leaf 和节点类型设置不同的颜色
            if (d.data.is_leaf) return "#8ecfc9"; // 叶子节点
            else if (d.data.name === mainTreeRoot.data.name) return "#beb8dc"; // 根节点
            else return "#82b0d2"; // 中间节点
        })
        .attr("r", 3)
        // Bug-fixed: 25-1-5
        // -----------------------------------------***------------------------------------------
        .attr("class", d => {
            if(d.isPathPoint === 0){
                return "normal";
            }
            else if(d.isPathPoint === 1){
                return "highlight";
            }
            else if(d.isPathPoint === 2){
                return "path1_normal";
            }
            else if(d.isPathPoint === 3){
                return "path1_highlight";
            }
            else if(d.isPathPoint === 4){
                return "path2_normal";
            }
            else if(d.isPathPoint === 5){
                return "path2_highlight";
            }
            else{
                return "normal";
            }
        })

        // -----------------------------------------***------------------------------------------
        // 添加鼠标悬停显示节点名称的事件
        .on("mouseover", function(event, d) { // 鼠标悬停事件
            const tooltip = d3.select("body").append("div") // 创建 tooltip 元素
                .attr("class", "tooltip")
                .style("position", "absolute")
                .style("background", "rgba(0,0,0,0.7)")
                .style("color", "white")
                .style("border-radius", "5px")
                .style("padding", "5px")
                .style("pointer-events", "none")
                .text(d.data.name); // 显示节点名称
            tooltip.style("left", (event.pageX + 5) + "px") // 设置 tooltip 位置
                .style("top", (event.pageY + 5) + "px");
        })
        .on("mouseout", function(d) { // 鼠标移开事件
            d3.select(".tooltip").remove(); // 移除 tooltip
        });


    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        // .text(d => {
        //     if (!d.children) {
        //         // 如果是叶子节点
        //         let cur_idx = name_idx_dict[d.data.name];
        //         if (cur_idx !== undefined) {
        //             // 如果已有
        //             return cur_idx;
        //         } else {
        //             // 如果没有
        //             name_idx_dict[d.data.name] = idx;
        //             idx++;
        //             return idx - 1;
        //         }
        //     }
        // })  // 为每个节点分配序号，从 1 开始
        .text(d => {
            if (d.data.is_leaf) {  // 只为叶子节点分配标号
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
            return "";  // 非叶子节点不显示标号
        })  // 为叶子节点分配序号，从 1 开始
        .attr("font-size", "8px")  // 设置字体大小
        .attr("font-family", "Arial, sans-serif")  // 设置字体为 Arial
        .attr("fill", "black");  // 设置字体颜色

    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    const datasPerRow = 3;
    let currentRow = document.createElement("tr");
    sortedEntries.forEach(([substance, idx]) => {
        const cell = document.createElement('td');
        cell.innerHTML = `<td>${idx}: ${substance}</td>`;
        currentRow.appendChild(cell);

        if(idx % datasPerRow === 0) {
            tbody.appendChild(currentRow);
            currentRow = document.createElement("tr");
        }
    });

    // 下载按钮
    // 下载SVG图像
    // Add download button
    const button = document.getElementById("downloadBtn");
    button.innerText = "Download SVG";
    button.addEventListener("click", () => {
        const svgNode = svg.node();
        // 获取页面中所有的 <style> 标签内容
        const styleSheets = document.querySelectorAll("style");
        let styleContent = "";
        styleSheets.forEach(sheet => {
            styleContent += sheet.innerHTML;
        });
        // 创建一个 <style> 元素并添加到 SVG 的 <defs> 中
        const styleElement = document.createElementNS("http://www.w3.org/2000/svg", "style");
        styleElement.innerHTML = styleContent;
        svgNode.querySelector("defs")?.appendChild(styleElement) || svgNode.insertBefore(styleElement, svgNode.firstChild);

        const serializer = new XMLSerializer();
        const svgBlob = new Blob([serializer.serializeToString(svg.node())], {type: "image/svg+xml"});
        const url = URL.createObjectURL(svgBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "chart.svg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    console.log("4 tree completed!");
}

function renderFiveTree(fiveTree){
    const mainTree = fiveTree['main'];
    const sonTree = fiveTree['son'];
    const path1 = fiveTree['path1'];
    const path2 = fiveTree['path2'];
    const blackTree = fiveTree['black_tree'];

    // size
    const width = 928;
    const height = width;
    const cx = width * 0.5; // adjust as needed to fit
    const cy = height * 0.5; // adjust as needed to fit
    const radius = Math.min(width, height) / 2 - 30;

    // Create a radial tree layout. The layout’s first dimension (x)
    // is the angle, while the second (y) is the radius.
    const treeLayout = d3.tree()
        .size([2 * Math.PI, radius])
        .separation((a, b) => (a.parent == b.parent ? 1 : 1) / a.depth);

    // Sort the tree and apply the layout.
    const mainTreeRoot = d3.hierarchy(mainTree);
    const sonTreeRoot = d3.hierarchy(sonTree);
    const path1TreeRoot = d3.hierarchy(path1);
    const path2TreeRoot = d3.hierarchy(path2);

    const blackTreeRoot = d3.hierarchy(blackTree);

    treeLayout(mainTreeRoot);

    const mainNodeMap = {};
    mainTreeRoot.descendants().forEach(node => {
      const key = node.parent
        ? `${node.depth}-${node.data.name}-${node.parent.data.name}`
        : `${node.depth}-${node.data.name}-root`;
      mainNodeMap[key] = node;
    });

    blackTreeRoot.descendants().forEach(node => {
      const key = node.parent
        ? `${node.depth}-${node.data.name}-${node.parent.data.name}`
        : `${node.depth}-${node.data.name}-root`;

      const correspondingNode = mainNodeMap[key];
      if (correspondingNode) {
        node.x = correspondingNode.x;
        node.y = correspondingNode.y;
      }
    });

    // 初始化大树所有节点的isPathPoint属性为false
    mainTreeRoot.each(d => d.isPathPoint = 0);

    // 2024/11/27
    // 0: main树
    // 1: 子树
    // 2: path1
    // 3: path2

    // 层次遍历获取小树的节点集合
    const sonTreeLevels = getNodesByLevel(sonTreeRoot);

    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths_v2(mainTreeRoot, sonTreeLevels, 1);

    // 层次遍历获取小树的节点集合
    const path1TreeLevels = getNodesByLevel(path1TreeRoot);

    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths_v2(mainTreeRoot, path1TreeLevels, 2);

    // 层次遍历获取小树的节点集合
    const path2TreeLevels = getNodesByLevel(path2TreeRoot);

    // 使用层序遍历匹配节点，并高亮路径
    highlightPaths_v2(mainTreeRoot, path2TreeLevels, 3);

    // 染色所有边
    // highlightLinks(mainTreeRoot.links());

    // Creates the SVG container.
    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-cx, -cy, width, height])
        .attr("style", "width: 100%; height: auto; font: 10px sans-serif;");

    // Append links.
    svg.append("g")
        .attr("fill", "none")
        .attr("stroke", "#555")
        .attr("stroke-opacity", 0.4)
        .attr("stroke-width", 1) // 修改边的粗细1.5
        .selectAll()
        .data(mainTreeRoot.links())
        .join("path")
        .attr("d", d3.linkRadial()
            .angle(d => d.x)
            .radius(d => d.y))
        .attr("class", d => {
            const source = d.source;
            const target = d.target;
            const num = target.isPathPoint;
            if(num === 1){
                return "highlightLinks";
            }
            else if (num === 2){
                return "path1Links";
            }
            else if (num === 3){
                return "path2Links";
            }
            else{
                return "normalLinks";
            }
        });

    // 12_13: Add black tree first and put big tree over the black tree
    const black_nodes = svg.append("g")
        .selectAll()
        .data(blackTreeRoot.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    black_nodes.append("circle")
        // 调节黑色轮廓粗细
        .attr("r", 4.25)
        .attr("class", d => "black_tree");

    // Append nodes.
    const nodes = svg.append("g")
        .selectAll()
        .data(mainTreeRoot.descendants())
        .join("g")
        .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`);

    nodes.append("circle")
        .attr("fill", d => {
            if (!d.children) return "#8ecfc9";// 叶子节点
            else if (d.data.name === mainTreeRoot.data.name) return "#beb8dc"; // 根节点
            else return "#82b0d2";// 中间节点
        })
        .attr("r", 4)
        .attr("class", d => {
            if(d.isPathPoint === 0){
                return "normal";
            }
            else if(d.isPathPoint === 1){
                return "highlight";
            }
            else if(d.isPathPoint === 2){
                return "path1";
            }
            else{
                return "path2";
            }
        });


    let idx = 1;
    const name_idx_dict = {};
    // Append Nodes' names
    nodes.append("text")
        .attr("dy", "0.31em")  // 设置垂直对齐，使文本居中
        .attr("x", d => d.x < Math.PI ? 6 : -6)  // 设置文本相对于节点的位置
        .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")  // 设置文本的对齐方式
        .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)  // 处理文本的方向
        .text(d => {
            if (!d.children) {
                // 如果是叶子节点
                let cur_idx = name_idx_dict[d.data.name];
                if (cur_idx !== undefined) {
                    // 如果已有
                    return cur_idx;
                } else {
                    // 如果没有
                    name_idx_dict[d.data.name] = idx;
                    idx++;
                    return idx - 1;
                }
            }
        })  // 为每个节点分配序号，从 1 开始
        .attr("font-size", "10px")  // 设置字体大小
        .attr("fill", "black");  // 设置字体颜色

    document.getElementById("tree-container").appendChild(svg.node());
    // document.body.appendChild(button); // Append button to document

    // 加入图例
    const sortedEntries = Object.entries(name_idx_dict).sort((a, b) => a[1] - b[1]);

    const tbody = document.getElementById("indices-container");

    // 遍历排序后的数组并生成表格行
    const datasPerRow = 3;
    let currentRow = document.createElement("tr");
    sortedEntries.forEach(([substance, idx]) => {
        const cell = document.createElement('td');
        cell.innerHTML = `<td>${idx}: ${substance}</td>`;
        currentRow.appendChild(cell);

        if(idx % datasPerRow === 0) {
            tbody.appendChild(currentRow);
            currentRow = document.createElement("tr");
        }
    });

    // 下载按钮
    // 下载SVG图像
    // Add download button
    const button = document.getElementById("downloadBtn");
    button.innerText = "Download SVG";
    button.addEventListener("click", () => {
        const svgNode = svg.node();
        // 获取页面中所有的 <style> 标签内容
        const styleSheets = document.querySelectorAll("style");
        let styleContent = "";
        styleSheets.forEach(sheet => {
            styleContent += sheet.innerHTML;
        });

            // 创建一个 <style> 元素并添加到 SVG 的 <defs> 中
        const styleElement = document.createElementNS("http://www.w3.org/2000/svg", "style");
        styleElement.innerHTML = styleContent;
        svgNode.querySelector("defs")?.appendChild(styleElement) || svgNode.insertBefore(styleElement, svgNode.firstChild);

        const serializer = new XMLSerializer();
        const svgBlob = new Blob([serializer.serializeToString(svg.node())], {type: "image/svg+xml"});
        const url = URL.createObjectURL(svgBlob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "chart.svg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    console.log("5 tree completed!");
}

function getNodesByLevel(root){
    const levels = {};
    root.each(d => {
        if (!levels[d.depth]){
            levels[d.depth] = [];
        }
        levels[d.depth].push(d);
    });
    return levels;
}

function highlightPaths(bigRoot, smallTreeLevels){
    const queue = [bigRoot];
    bigRoot.isPathPoint = true;

    while (queue.length > 0){
        const currentNode = queue.shift();

        if(currentNode.parent && currentNode.parent.isPathPoint){
            const depth = currentNode.depth;
            const smallNodesAtDepth = smallTreeLevels[depth] || [];

            smallNodesAtDepth.forEach(smallNode => {
                if (currentNode.data.name === smallNode.data.name){
                    currentNode.isPathPoint = true;
                }
            })
        }

        // 子节点加入队列，进行层序遍历
        if(currentNode.children){
            currentNode.children.forEach(child => queue.push(child));
        }
    }
}

// 用来对节点进行染色
function highlightPaths_v2(bigRoot, smallTreeLevels, value){
    const queue = [bigRoot];
    bigRoot.isPathPoint = value;

    while (queue.length > 0){
        const currentNode = queue.shift();

        if(currentNode.parent !== null && currentNode.parent.isPathPoint === value){
            const depth = currentNode.depth;
            const smallNodesAtDepth = smallTreeLevels[depth] || [];

            smallNodesAtDepth.forEach(smallNode => {
                if (currentNode.data.name === smallNode.data.name){
                    currentNode.isPathPoint = value;
                }
            })
        }

        // 子节点加入队列，进行层序遍历
        if(currentNode.children){
            currentNode.children.forEach(child => queue.push(child));
        }
    }
}

// 用来对节点进行染色
function highlightPaths_v3(bigRoot, smallTreeLevels, value, neg_value, superior_value){
    const queue = [bigRoot];
    bigRoot.isPathPoint = neg_value;

    while (queue.length > 0){
        const currentNode = queue.shift();

        // 父-子-结果
        // value or neg_value - superior_value - neg_value
        // value or neg_value - not superior_value - value
        // not value and not neg_value - don't dyed
        if(currentNode.parent !== null && ((currentNode.parent.isPathPoint === neg_value)||(currentNode.parent.isPathPoint ===value))){
            const depth = currentNode.depth;
            const smallNodesAtDepth = smallTreeLevels[depth] || [];

            smallNodesAtDepth.forEach(smallNode => {
                if (currentNode.data.name === smallNode.data.name){
                    if(currentNode.isPathPoint === superior_value){
                        currentNode.isPathPoint = neg_value;
                    }
                    else {
                        currentNode.isPathPoint = value;
                    }
                }
            })
        }

        // 子节点加入队列，进行层序遍历
        if(currentNode.children){
            currentNode.children.forEach(child => queue.push(child));
        }
    }
}

// 用来对边进行染色
// function highlightLinks(links){
//     // source, target
//     // 遍历所有边，如果source和target都是同一个值，那么把这个边也设为该值
//     links.forEach(link => {
//         if(link.source.isPathPoint === link.target.isPathPoint){
//             link.isPathPoint = link.target.isPathPoint;
//         }
//         else{
//             link.isPathPoint = 0;
//         }
//     })
// }

function highlightLinks(links) {
    links.forEach(link => {
        // 获取绑定的数据
        let data = d3.select(link).datum();

        // 修改数据
        if (link.source.isPathPoint === link.target.isPathPoint) {
            data.isPathPoint = link.target.isPathPoint;
        } else {
            data.isPathPoint = 0;
        }

        // 更新绑定的数据
        d3.select(link).datum(data);
    });
}

function download(json, filename) {
    const jsonString = JSON.stringify(json);

    const blob = new Blob([jsonString], { type: 'application/json' });

    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(blob);

    // 文件名
    downloadLink.download = filename;

    // 隐藏链接
    downloadLink.style.display = 'none';

    // 添加到页面并点击下载
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function exportTableToJson(filename) {
    let ret = {"data": []};
    let json = ret["data"];
    let rows = document.querySelectorAll("table tr");

    // 遍历表格的每一行
    for (let i = 0; i < rows.length; i++) {
        let cols = rows[i].querySelectorAll("td");
        // 遍历每一行的列
        for (let j = 0; j < cols.length; j++) {
            let row = cols[j].innerText.split(":");
            json.push(row[1]);
        }
    }
    console.log(ret);

    // 下载CSV文件
    download(ret, filename);
}


