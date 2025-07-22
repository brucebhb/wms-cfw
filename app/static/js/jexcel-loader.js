/**
 * jExcel库加载脚本
 * 用于确保jexcel库正确加载
 */

console.log('jExcel加载脚本已执行');

// 检查jexcel是否已定义
if (typeof jexcel === 'undefined') {
    console.log('jexcel未定义，尝试使用jspreadsheet');
    
    // 检查jspreadsheet是否已定义
    if (typeof jspreadsheet !== 'undefined') {
        window.jexcel = jspreadsheet;
        console.log('已将jspreadsheet赋值给jexcel');
    } else {
        console.error('jexcel和jspreadsheet都未定义，尝试加载jexcel库');
        
        // 尝试加载jexcel库
        function loadJExcelLibrary() {
            // 加载CSS
            const jexcelCSS = document.createElement('link');
            jexcelCSS.rel = 'stylesheet';
            jexcelCSS.type = 'text/css';
            jexcelCSS.href = 'https://cdn.jsdelivr.net/npm/jexcel/dist/jexcel.min.css';
            document.head.appendChild(jexcelCSS);
            
            const jsuitesCSS = document.createElement('link');
            jsuitesCSS.rel = 'stylesheet';
            jsuitesCSS.type = 'text/css';
            jsuitesCSS.href = 'https://cdn.jsdelivr.net/npm/jsuites/dist/jsuites.min.css';
            document.head.appendChild(jsuitesCSS);
            
            // 加载jsuites.js
            const jsuitesScript = document.createElement('script');
            jsuitesScript.src = 'https://cdn.jsdelivr.net/npm/jsuites/dist/jsuites.min.js';
            document.head.appendChild(jsuitesScript);
            
            // 等待jsuites加载完成后加载jexcel
            jsuitesScript.onload = function() {
                console.log('jsuites库加载完成');
                
                const jexcelScript = document.createElement('script');
                jexcelScript.src = 'https://cdn.jsdelivr.net/npm/jexcel/dist/jexcel.min.js';
                document.head.appendChild(jexcelScript);
                
                jexcelScript.onload = function() {
                    console.log('jexcel库加载完成');
                    
                    // 触发jexcel加载完成事件
                    const event = new CustomEvent('jexcel-loaded');
                    document.dispatchEvent(event);
                };
                
                jexcelScript.onerror = function() {
                    console.error('jexcel库加载失败');
                };
            };
            
            jsuitesScript.onerror = function() {
                console.error('jsuites库加载失败');
            };
        }
        
        // 执行加载
        loadJExcelLibrary();
    }
} else {
    console.log('jexcel已定义，无需加载');
}

// 导出jexcel检查函数
window.checkJExcel = function() {
    if (typeof jexcel === 'function') {
        console.log('jexcel可用');
        return true;
    } else if (typeof jspreadsheet === 'function') {
        window.jexcel = jspreadsheet;
        console.log('已将jspreadsheet赋值给jexcel');
        return true;
    } else {
        console.error('jexcel和jspreadsheet都不可用');
        return false;
    }
}; 