/**
 * 调试控制脚本
 * 统一管理所有调试输出，提高生产环境性能
 */

(function() {
    'use strict';
    
    // 生产环境配置
    const PRODUCTION_MODE = false; // 临时启用调试输出来排查问题
    
    // 保存原始console方法
    const originalConsole = {
        log: console.log,
        warn: console.warn,
        error: console.error,
        info: console.info,
        debug: console.debug
    };
    
    // 需要保留的重要日志关键词
    const importantKeywords = [
        '✅ jQuery加载成功',
        '🚀 整合性能管理器',
        '❌', // 错误信息
        'Error', 'error',
        'Failed', 'failed',
        '页面加载时间',
        '性能优化已启用'
    ];
    
    // 需要过滤的调试信息关键词
    const debugKeywords = [
        '🔍 DEBUG:',
        '📊 找到',
        '📋 卡片',
        '🔍 检查样式表',
        '⚠️ 无法访问样式表',
        '❌ 未找到',
        '🔧 检测到页面加载卡住',
        '✅ 加载指示器已隐藏'
    ];
    
    // 检查是否是重要日志
    function isImportantLog(message) {
        const messageStr = String(message);
        return importantKeywords.some(keyword => messageStr.includes(keyword));
    }
    
    // 检查是否是调试日志
    function isDebugLog(message) {
        const messageStr = String(message);
        return debugKeywords.some(keyword => messageStr.includes(keyword));
    }
    
    // 过滤控制台输出
    function filterConsoleOutput(originalMethod, methodName) {
        return function(...args) {
            if (!PRODUCTION_MODE) {
                // 开发模式：显示所有日志
                return originalMethod.apply(console, args);
            }
            
            // 生产模式：过滤调试日志
            const firstArg = args[0];
            
            // 保留重要日志
            if (isImportantLog(firstArg)) {
                return originalMethod.apply(console, args);
            }
            
            // 过滤调试日志
            if (isDebugLog(firstArg)) {
                return; // 不输出
            }
            
            // 保留错误和警告
            if (methodName === 'error' || methodName === 'warn') {
                return originalMethod.apply(console, args);
            }
            
            // 其他日志根据长度过滤
            const messageStr = String(firstArg);
            if (messageStr.length > 100) {
                // 过滤过长的调试信息
                return;
            }
            
            // 显示简短的重要信息
            return originalMethod.apply(console, args);
        };
    }
    
    // 应用过滤器
    if (PRODUCTION_MODE) {
        console.log = filterConsoleOutput(originalConsole.log, 'log');
        console.info = filterConsoleOutput(originalConsole.info, 'info');
        console.debug = filterConsoleOutput(originalConsole.debug, 'debug');
        console.warn = filterConsoleOutput(originalConsole.warn, 'warn');
        console.error = filterConsoleOutput(originalConsole.error, 'error');
        
        console.log('🔇 调试输出已优化，减少控制台噪音');
    }
    
    // 提供控制台命令
    window.enableDebugMode = function() {
        console.log = originalConsole.log;
        console.warn = originalConsole.warn;
        console.error = originalConsole.error;
        console.info = originalConsole.info;
        console.debug = originalConsole.debug;
        console.log('🔊 调试模式已启用');
    };
    
    window.disableDebugMode = function() {
        console.log = filterConsoleOutput(originalConsole.log, 'log');
        console.info = filterConsoleOutput(originalConsole.info, 'info');
        console.debug = filterConsoleOutput(originalConsole.debug, 'debug');
        console.warn = filterConsoleOutput(originalConsole.warn, 'warn');
        console.error = filterConsoleOutput(originalConsole.error, 'error');
        console.log('🔇 调试模式已禁用');
    };
    
    // 性能监控
    let logCount = 0;
    const originalLog = console.log;
    
    // 监控日志数量
    setInterval(() => {
        if (logCount > 50) {
            console.warn(`⚠️ 检测到大量日志输出 (${logCount}条)，可能影响性能`);
        }
        logCount = 0;
    }, 10000); // 每10秒检查一次
    
})();
