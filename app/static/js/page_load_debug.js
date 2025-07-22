
// 页面加载调试助手
class PageLoadDebugHelper {
    constructor() {
        this.startTime = Date.now();
        this.events = [];
        this.ajaxRequests = [];
        
        this.init();
    }
    
    init() {
        // 监控页面加载事件
        this.logEvent('页面开始加载');
        
        $(document).ready(() => {
            this.logEvent('DOM加载完成');
        });
        
        $(window).on('load', () => {
            this.logEvent('页面完全加载');
            this.showSummary();
        });
        
        // 监控AJAX请求
        this.monitorAjax();
    }
    
    logEvent(event) {
        let timestamp = Date.now() - this.startTime;
        this.events.push({
            event: event,
            timestamp: timestamp,
            time: new Date().toLocaleTimeString()
        });
        console.log(`[${timestamp}ms] ${event}`);
    }
    
    monitorAjax() {
        let self = this;
        
        // 监控jQuery AJAX
        $(document).ajaxStart(function() {
            self.logEvent('AJAX请求开始');
        });
        
        $(document).ajaxComplete(function(event, xhr, settings) {
            self.logEvent(`AJAX请求完成: ${settings.url}`);
            self.ajaxRequests.push({
                url: settings.url,
                status: xhr.status,
                time: Date.now() - self.startTime
            });
        });
        
        $(document).ajaxError(function(event, xhr, settings, error) {
            self.logEvent(`AJAX请求失败: ${settings.url} - ${error}`);
        });
    }
    
    showSummary() {
        let totalTime = Date.now() - this.startTime;
        console.group('页面加载总结');
        console.log(`总加载时间: ${totalTime}ms`);
        console.log('加载事件:', this.events);
        console.log('AJAX请求:', this.ajaxRequests);
        
        if (totalTime > 5000) {
            console.warn('页面加载时间过长，建议优化');
        }
        
        console.groupEnd();
    }
    
    // 手动触发调试信息
    debug() {
        this.showSummary();
        return {
            totalTime: Date.now() - this.startTime,
            events: this.events,
            ajaxRequests: this.ajaxRequests
        };
    }
}

// 在开发环境中启用调试助手
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.pageLoadDebugHelper = new PageLoadDebugHelper();
    
    // 添加全局调试函数
    window.debugPageLoad = function() {
        return window.pageLoadDebugHelper.debug();
    };
}
