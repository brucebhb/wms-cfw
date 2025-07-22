
// 加载优化脚本
(function() {
    // 1. 预加载关键资源
    function preloadCriticalResources() {
        var criticalResources = [
            'https://cdn.bootcdn.net/ajax/libs/handsontable/13.0.0/handsontable.full.min.js',
            'https://cdn.bootcdn.net/ajax/libs/handsontable/13.0.0/handsontable.full.min.css'
        ];
        
        criticalResources.forEach(function(url) {
            var link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            document.head.appendChild(link);
        });
    }
    
    // 2. 延迟加载非关键内容
    function lazyLoadNonCritical() {
        // 延迟加载图片
        var images = document.querySelectorAll('img[data-src]');
        images.forEach(function(img) {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
        });
        
        // 延迟初始化非关键组件
        setTimeout(function() {
            // 这里可以放置非关键的初始化代码
        }, 100);
    }
    
    // 3. 优化表格渲染
    function optimizeTableRendering() {
        // 如果页面有大量数据，使用虚拟滚动
        var tables = document.querySelectorAll('.large-table');
        tables.forEach(function(table) {
            // 实现虚拟滚动逻辑
            console.log('优化大表格渲染:', table);
        });
    }
    
    // 4. 缓存优化
    function setupCaching() {
        // 设置本地存储缓存
        if ('localStorage' in window) {
            var cacheKey = 'app_cache_' + window.location.pathname;
            var cached = localStorage.getItem(cacheKey);
            
            if (cached) {
                console.log('使用缓存数据');
                // 可以在这里使用缓存数据
            }
        }
    }
    
    // 初始化优化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            preloadCriticalResources();
            lazyLoadNonCritical();
            optimizeTableRendering();
            setupCaching();
        });
    } else {
        preloadCriticalResources();
        lazyLoadNonCritical();
        optimizeTableRendering();
        setupCaching();
    }
})();
