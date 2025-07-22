
// 页面性能监控
(function() {
    var startTime = performance.now();
    
    // 监控页面加载完成
    window.addEventListener('load', function() {
        var loadTime = performance.now() - startTime;
        console.log('页面加载时间:', loadTime.toFixed(2) + 'ms');
        
        // 如果加载时间超过3秒，显示提示
        if (loadTime > 3000) {
            console.warn('页面加载较慢，建议优化');
            
            // 可选：显示用户提示
            var slowLoadingNotice = document.createElement('div');
            slowLoadingNotice.innerHTML = '页面加载较慢，正在优化中...';
            slowLoadingNotice.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #ffc107; padding: 10px; border-radius: 5px; z-index: 9999; font-size: 12px;';
            document.body.appendChild(slowLoadingNotice);
            
            setTimeout(function() {
                document.body.removeChild(slowLoadingNotice);
            }, 3000);
        }
    });
    
    // 监控资源加载
    window.addEventListener('load', function() {
        var resources = performance.getEntriesByType('resource');
        var slowResources = resources.filter(function(r) {
            return r.duration > 1000; // 超过1秒的资源
        });
        
        if (slowResources.length > 0) {
            console.warn('发现慢资源:', slowResources.map(function(r) {
                return {
                    name: r.name.split('/').pop(),
                    duration: r.duration.toFixed(2) + 'ms'
                };
            }));
        }
    });
    
    // 监控Handsontable加载
    var checkHandsontable = function() {
        if (typeof Handsontable !== 'undefined') {
            console.log('Handsontable加载完成');
        } else {
            console.log('等待Handsontable加载...');
            setTimeout(checkHandsontable, 100);
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkHandsontable);
    } else {
        checkHandsontable();
    }
})();
