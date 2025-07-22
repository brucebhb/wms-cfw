
// 全局CSRF令牌处理
window.CSRFToken = {
    getToken: function() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    },
    
    setupAjax: function() {
        // 为所有AJAX请求添加CSRF令牌
        const token = this.getToken();
        
        // jQuery设置
        if (typeof $ !== 'undefined') {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", token);
                    }
                }
            });
        }
        
        // Fetch API包装
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            if (options.method && options.method.toUpperCase() !== 'GET') {
                options.headers = options.headers || {};
                options.headers['X-CSRFToken'] = token;
            }
            return originalFetch(url, options);
        };
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.CSRFToken.setupAjax();
});
