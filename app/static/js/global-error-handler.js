/**
 * 全局错误处理脚本
 * 拦截并处理JavaScript错误，防止页面崩溃
 */
(function() {
    console.log('全局错误处理脚本已加载');
    
    // 安装全局错误处理程序
    window.addEventListener('error', function(event) {
        console.error('捕获到全局错误:', event.error);
        
        // 阻止浏览器默认错误处理
        event.preventDefault();
        
        // 记录错误
        logError(event.error);
        
        // 返回false以阻止错误冒泡
        return false;
    }, true);
    
    // 安装Promise错误处理程序
    window.addEventListener('unhandledrejection', function(event) {
        console.error('捕获到未处理的Promise拒绝:', event.reason);
        
        // 阻止默认处理
        event.preventDefault();
        
        // 记录错误
        logError(event.reason);
        
        // 返回false以阻止错误冒泡
        return false;
    });
    
    // 覆盖console.error以确保错误不会导致页面崩溃
    const originalConsoleError = console.error;
    console.error = function() {
        try {
            originalConsoleError.apply(console, arguments);
        } catch (e) {
            // 如果原始console.error出错，使用更安全的方法
            const args = Array.from(arguments).map(arg => {
                try {
                    return typeof arg === 'object' ? JSON.stringify(arg) : String(arg);
                } catch (e) {
                    return 'UNSERIALIZABLE OBJECT';
                }
            });
            originalConsoleError.call(console, 'ERROR:', args.join(' '));
        }
    };
    
    // 记录错误函数
    function logError(error) {
        try {
            // 创建错误消息
            let errorMessage = '';
            
            if (typeof error === 'object' && error !== null) {
                if (error instanceof Error) {
                    errorMessage = `错误: ${error.message}\n堆栈: ${error.stack || '无堆栈信息'}`;
                } else {
                    try {
                        errorMessage = JSON.stringify(error);
                    } catch (e) {
                        errorMessage = '无法序列化的错误对象';
                    }
                }
            } else {
                errorMessage = String(error);
            }
            
            // 输出到控制台
            console.log('错误已被全局处理器捕获:', errorMessage);
            
            // 如果是语法错误，不显示给用户
            if (error instanceof SyntaxError) {
                console.log('检测到语法错误，已静默处理');
                return;
            }
            
            // 检查是否为特定的try语法错误
            if (errorMessage.includes('Missing catch') || 
                errorMessage.includes('finally after try')) {
                console.log('检测到try语句语法错误，已静默处理');
                return;
            }
            
            // TODO: 可以添加将错误发送到服务器的代码
        } catch (e) {
            // 即使记录错误的过程中出错，也不要让它崩溃
            console.log('记录错误时发生异常:', e);
        }
    }
    
    // 重写setTimeout和setInterval，防止回调中的错误导致页面崩溃
    const originalSetTimeout = window.setTimeout;
    window.setTimeout = function(callback, timeout) {
        const args = Array.prototype.slice.call(arguments, 2);
        
        // 如果回调是函数，包装它以捕获错误
        if (typeof callback === 'function') {
            const wrappedCallback = function() {
                try {
                    callback.apply(this, args);
                } catch (e) {
                    console.error('setTimeout回调中出错:', e);
                }
            };
            return originalSetTimeout.call(window, wrappedCallback, timeout);
        } else {
            return originalSetTimeout.apply(window, arguments);
        }
    };
    
    const originalSetInterval = window.setInterval;
    window.setInterval = function(callback, timeout) {
        const args = Array.prototype.slice.call(arguments, 2);
        
        // 如果回调是函数，包装它以捕获错误
        if (typeof callback === 'function') {
            const wrappedCallback = function() {
                try {
                    callback.apply(this, args);
                } catch (e) {
                    console.error('setInterval回调中出错:', e);
                }
            };
            return originalSetInterval.call(window, wrappedCallback, timeout);
        } else {
            return originalSetInterval.apply(window, arguments);
        }
    };
    
    // 如果jQuery存在，包装jQuery的ready和事件处理函数
    if (window.jQuery) {
        const $ = window.jQuery;
        
        // 包装jQuery ready函数
        const originalReady = $.fn.ready;
        if (typeof originalReady === 'function') {
            $.fn.ready = function(fn) {
                return originalReady.call(this, function() {
                    try {
                        fn();
                    } catch (e) {
                        console.error('jQuery ready回调中出错:', e);
                    }
                });
            };
        }
        
        // 包装jQuery的事件绑定函数
        const originalOn = $.fn.on;
        if (typeof originalOn === 'function') {
            $.fn.on = function() {
                const args = Array.prototype.slice.call(arguments);
                
                // 查找并包装事件处理函数
                for (let i = 0; i < args.length; i++) {
                    if (typeof args[i] === 'function') {
                        const originalHandler = args[i];
                        args[i] = function() {
                            try {
                                return originalHandler.apply(this, arguments);
                            } catch (e) {
                                console.error('jQuery事件处理程序中出错:', e);
                                return false;
                            }
                        };
                    }
                }
                
                return originalOn.apply(this, args);
            };
        }
        
        console.log('jQuery事件处理已增强');
    }
    
    console.log('全局错误处理程序已安装');
})(); 