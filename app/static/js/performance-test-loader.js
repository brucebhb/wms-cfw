/**
 * 性能优化测试加载器
 * 用于测试和验证性能优化脚本的加载状态
 */

(function() {
    'use strict';
    
    console.log('🧪 性能测试加载器启动');
    
    // 等待一段时间后检查各个组件的加载状态
    setTimeout(() => {
        checkLoadingStatus();
    }, 5000);
    
    function checkLoadingStatus() {
        console.log('🔍 检查性能组件加载状态:');
        
        // 检查安全性能优化器
        if (window.safePerformanceOptimizer) {
            console.log('✅ 安全性能优化器已加载');
        } else {
            console.log('❌ 安全性能优化器未加载');
        }
        
        // 检查性能监控面板
        if (window.performanceDashboard) {
            console.log('✅ 性能监控面板已加载');
        } else {
            console.log('❌ 性能监控面板未加载');
        }

        // 检查性能配置
        if (window.PerformanceConfig) {
            console.log('✅ 性能配置已加载');
        } else {
            console.log('❌ 性能配置未加载');
        }

        // 检查统一性能管理器
        if (window.unifiedPerformanceManager || window.performanceManager) {
            console.log('✅ 统一性能管理器已加载');
        } else {
            console.log('❌ 统一性能管理器未加载');
        }

        // 检查自动性能修复器
        if (window.autoPerformanceFixer) {
            console.log('✅ 自动性能修复器已加载');
        } else {
            console.log('❌ 自动性能修复器未加载');
        }
        
        // 检查后端入库增强
        if (window.refreshTableStyles) {
            console.log('✅ 后端入库增强已加载');
        } else {
            console.log('❌ 后端入库增强未加载');
        }
        
        // 检查菜单事件管理器
        if (window.MenuEventManager) {
            console.log('✅ 菜单事件管理器已加载');
        } else {
            console.log('❌ 菜单事件管理器未加载');
        }
        
        // 提供手动初始化功能
        window.manualInitPerformance = function() {
            console.log('🔧 手动初始化性能组件...');
            
            if (!window.performanceDashboard && typeof PerformanceDashboard !== 'undefined') {
                window.performanceDashboard = new PerformanceDashboard();
                console.log('✅ 手动创建性能监控面板');
            }
            
            if (!window.safePerformanceOptimizer && typeof SafePerformanceOptimizer !== 'undefined') {
                window.safePerformanceOptimizer = new SafePerformanceOptimizer();
                console.log('✅ 手动创建安全性能优化器');
            }
        };
        
        // 提供测试功能
        window.testPerformanceComponents = function() {
            console.log('🧪 测试性能组件功能...');
            
            if (window.performanceDashboard) {
                try {
                    window.performanceDashboard.show();
                    console.log('✅ 性能面板显示测试成功');
                    setTimeout(() => {
                        window.performanceDashboard.hide();
                        console.log('✅ 性能面板隐藏测试成功');
                    }, 2000);
                } catch (e) {
                    console.log('❌ 性能面板测试失败:', e);
                }
            }
            
            if (window.safePerformanceOptimizer) {
                try {
                    window.safePerformanceOptimizer.manualOptimize();
                    console.log('✅ 安全优化器测试成功');
                } catch (e) {
                    console.log('❌ 安全优化器测试失败:', e);
                }
            }
        };
        
        console.log('💡 可用命令:');
        console.log('  manualInitPerformance() - 手动初始化性能组件');
        console.log('  testPerformanceComponents() - 测试性能组件功能');
    }
    
    // 监听页面加载完成
    if (document.readyState === 'complete') {
        console.log('📄 页面已完全加载');
    } else {
        window.addEventListener('load', () => {
            console.log('📄 页面加载完成');
        });
    }
    
    console.log('🚀 性能测试加载器已就绪');
})();
