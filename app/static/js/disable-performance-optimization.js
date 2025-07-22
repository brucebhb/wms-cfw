/**
 * 紧急禁用性能优化脚本
 * 如果性能优化影响了页面功能，可以使用此脚本快速禁用
 */

(function() {
    'use strict';
    
    console.log('🛑 禁用性能优化脚本已加载');
    
    // 禁用自动性能修复器
    if (window.autoPerformanceFixer) {
        window.autoPerformanceFixer.disable();
        console.log('🛑 已禁用自动性能修复器');
    }
    
    // 禁用性能监控面板
    if (window.performanceDashboard) {
        window.performanceDashboard.hide();
        console.log('🛑 已隐藏性能监控面板');
    }
    
    // 禁用性能自动启动
    if (window.PerformanceAutoStart) {
        // 标记为禁用状态
        window.PerformanceAutoStart.disabled = true;
        console.log('🛑 已禁用性能自动启动');
    }
    
    // 清理可能的性能优化定时器
    const highestTimeoutId = setTimeout(function(){}, 0);
    for (let i = 0; i < highestTimeoutId; i++) {
        clearTimeout(i);
    }
    
    const highestIntervalId = setInterval(function(){}, 9999);
    for (let i = 0; i < highestIntervalId; i++) {
        clearInterval(i);
    }
    
    console.log('🛑 已清理所有定时器');
    
    // 恢复原始的控制台方法（如果被修改）
    if (window.originalConsole) {
        window.console = window.originalConsole;
        console.log('🛑 已恢复原始控制台');
    }
    
    // 移除性能优化相关的事件监听器
    document.removeEventListener('visibilitychange', arguments.callee);
    window.removeEventListener('load', arguments.callee);
    window.removeEventListener('popstate', arguments.callee);
    
    console.log('🛑 已移除性能优化事件监听器');
    
    // 显示禁用确认
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #dc3545;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 10000;
        font-family: Arial, sans-serif;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notification.innerHTML = `
        <strong>🛑 性能优化已禁用</strong><br>
        <small>页面功能应该恢复正常</small>
    `;
    
    document.body.appendChild(notification);
    
    // 3秒后自动移除通知
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
    
    console.log('✅ 性能优化禁用完成');
})();
