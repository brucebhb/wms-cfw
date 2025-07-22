/**
 * 自动启用性能优化脚本
 * 确保所有性能优化功能自动启用，无需手动操作
 */

(function() {
    'use strict';
    
    console.log('🚀 自动启用性能优化系统...');
    
    // 等待页面完全加载
    function initAutoPerformance() {
        // 1. 自动启用安全性能优化器
        if (window.safePerformanceOptimizer) {
            window.safePerformanceOptimizer.enable();
            console.log('✅ 安全性能优化器已自动启用');
        }
        
        // 2. 自动显示性能监控按钮
        addPerformanceButton();
        
        // 3. 自动启用表格优化
        if (window.refreshTableStyles) {
            window.refreshTableStyles();
            console.log('✅ 表格样式已自动优化');
        }
        
        // 4. 自动启用消息系统测试
        if (typeof window.showMessage === 'function') {
            setTimeout(() => {
                window.showMessage('success', '🚀 性能优化系统已自动启用！', 3000);
            }, 2000);
        }
        
        // 5. 定期自动优化
        startAutoOptimization();
        
        console.log('🎉 所有性能优化功能已自动启用');
    }
    
    // 添加性能监控按钮到页面
    function addPerformanceButton() {
        // 检查是否已存在按钮
        if (document.getElementById('auto-performance-btn')) {
            return;
        }
        
        const button = document.createElement('button');
        button.id = 'auto-performance-btn';
        button.innerHTML = '🚀';
        button.title = '性能监控面板 (Ctrl+Shift+P)';
        button.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 50%;
            background: linear-gradient(45deg, #007bff, #0056b3);
            color: white;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 2px 10px rgba(0,123,255,0.3);
            transition: all 0.3s ease;
        `;
        
        // 悬停效果
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'scale(1.1)';
            button.style.boxShadow = '0 4px 15px rgba(0,123,255,0.5)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'scale(1)';
            button.style.boxShadow = '0 2px 10px rgba(0,123,255,0.3)';
        });
        
        // 点击事件
        button.addEventListener('click', () => {
            if (window.performanceDashboard) {
                window.performanceDashboard.toggle();
            } else {
                window.showMessage('info', '性能监控面板正在加载中...');
            }
        });
        
        document.body.appendChild(button);
        console.log('✅ 性能监控按钮已添加');
    }
    
    // 启动自动优化
    function startAutoOptimization() {
        // 每30秒自动执行一次轻量级优化
        setInterval(() => {
            if (window.safePerformanceOptimizer) {
                // 执行轻量级优化
                window.safePerformanceOptimizer.performLightOptimization();
                console.log('🔄 自动轻量级优化已执行');
            }
        }, 30000); // 30秒
        
        // 每5分钟执行一次完整优化
        setInterval(() => {
            if (window.safePerformanceOptimizer) {
                window.safePerformanceOptimizer.manualOptimize();
                console.log('🔧 自动完整优化已执行');
            }
        }, 300000); // 5分钟
        
        console.log('⏰ 自动优化定时器已启动');
    }
    
    // 提供手动控制接口
    window.autoPerformanceControl = {
        enable: function() {
            initAutoPerformance();
            console.log('✅ 性能优化已手动启用');
        },
        
        disable: function() {
            if (window.safePerformanceOptimizer) {
                window.safePerformanceOptimizer.disable();
            }
            const button = document.getElementById('auto-performance-btn');
            if (button) {
                button.remove();
            }
            console.log('🛑 性能优化已手动禁用');
        },
        
        status: function() {
            const status = {
                safeOptimizer: !!window.safePerformanceOptimizer,
                dashboard: !!window.performanceDashboard,
                config: !!window.PerformanceConfig,
                unifiedManager: !!window.unifiedPerformanceManager,
                tableEnhancement: !!window.refreshTableStyles,
                messageSystem: typeof window.showMessage === 'function'
            };
            console.table(status);
            return status;
        },
        
        optimize: function() {
            if (window.safePerformanceOptimizer) {
                window.safePerformanceOptimizer.manualOptimize();
                window.showMessage('success', '手动优化已完成！');
            }
        }
    };
    
    // 页面加载完成后自动启用
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initAutoPerformance, 3000); // 延迟3秒确保其他脚本已加载
        });
    } else {
        setTimeout(initAutoPerformance, 3000);
    }
    
    // 提供控制台快捷命令
    window.enablePerformance = () => window.autoPerformanceControl.enable();
    window.disablePerformance = () => window.autoPerformanceControl.disable();
    window.performanceStatus = () => window.autoPerformanceControl.status();
    window.optimizeNow = () => window.autoPerformanceControl.optimize();
    
    console.log('🎮 自动性能控制器已加载');
    console.log('💡 可用命令: enablePerformance(), disablePerformance(), performanceStatus(), optimizeNow()');
})();
