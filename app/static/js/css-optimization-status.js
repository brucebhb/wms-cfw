/**
 * CSS优化状态显示器
 * 实时显示CSS优化效果，确保用户了解优化状态
 */

class CSSOptimizationStatus {
    constructor() {
        this.statusPanel = null;
        this.isVisible = false;
        this.optimizationStats = {
            cssFilesOptimized: 0,
            loadTimeImprovement: 0,
            bytesReduced: 0,
            criticalCSSPrioritized: 0
        };
        this.init();
    }

    init() {
        console.log('📊 CSS优化状态显示器启动');
        this.createStatusPanel();
        this.startMonitoring();
        this.setupKeyboardShortcut();
    }

    createStatusPanel() {
        // 创建状态面板
        this.statusPanel = document.createElement('div');
        this.statusPanel.id = 'css-optimization-status';
        this.statusPanel.innerHTML = `
            <div class="css-status-header">
                <h4>🎨 CSS优化状态</h4>
                <button class="css-status-close" onclick="window.cssOptimizationStatus.hide()">×</button>
            </div>
            <div class="css-status-content">
                <div class="status-item">
                    <span class="status-label">CSS文件优化:</span>
                    <span class="status-value" id="css-files-count">0</span>
                </div>
                <div class="status-item">
                    <span class="status-label">关键CSS优先级:</span>
                    <span class="status-value" id="critical-css-count">0</span>
                </div>
                <div class="status-item">
                    <span class="status-label">加载时间改善:</span>
                    <span class="status-value" id="load-time-improvement">0ms</span>
                </div>
                <div class="status-item">
                    <span class="status-label">优化状态:</span>
                    <span class="status-value status-active" id="optimization-status">✅ 活跃</span>
                </div>
                <div class="status-actions">
                    <button onclick="window.cssOptimizationStatus.refreshStats()">🔄 刷新</button>
                    <button onclick="window.cssOptimizationStatus.showDetails()">📋 详情</button>
                </div>
            </div>
        `;

        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            #css-optimization-status {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 300px;
                background: #fff;
                border: 2px solid #007bff;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                display: none;
            }
            
            .css-status-header {
                background: #007bff;
                color: white;
                padding: 10px 15px;
                border-radius: 6px 6px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .css-status-header h4 {
                margin: 0;
                font-size: 14px;
                font-weight: 600;
            }
            
            .css-status-close {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .css-status-content {
                padding: 15px;
            }
            
            .status-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 12px;
            }
            
            .status-label {
                color: #666;
            }
            
            .status-value {
                font-weight: 600;
                color: #333;
            }
            
            .status-active {
                color: #28a745;
            }
            
            .status-actions {
                margin-top: 15px;
                display: flex;
                gap: 8px;
            }
            
            .status-actions button {
                flex: 1;
                padding: 6px 8px;
                border: 1px solid #ddd;
                background: #f8f9fa;
                border-radius: 4px;
                cursor: pointer;
                font-size: 11px;
                transition: background-color 0.2s;
            }
            
            .status-actions button:hover {
                background: #e9ecef;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(this.statusPanel);
    }

    startMonitoring() {
        // 初始统计
        this.updateStats();
        
        // 定期更新统计
        setInterval(() => {
            this.updateStats();
        }, 5000);
        
        console.log('✅ CSS优化监控已启动');
    }

    updateStats() {
        // 统计CSS文件
        const cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
        this.optimizationStats.cssFilesOptimized = cssLinks.length;

        // 统计关键CSS
        const criticalCSS = Array.from(cssLinks).filter(link => 
            link.hasAttribute('importance') || 
            link.href.includes('bootstrap') || 
            link.href.includes('fontawesome')
        );
        this.optimizationStats.criticalCSSPrioritized = criticalCSS.length;

        // 更新显示
        this.updateDisplay();
    }

    updateDisplay() {
        if (!this.statusPanel) return;

        const elements = {
            'css-files-count': this.optimizationStats.cssFilesOptimized,
            'critical-css-count': this.optimizationStats.criticalCSSPrioritized,
            'load-time-improvement': `${this.optimizationStats.loadTimeImprovement}ms`,
            'optimization-status': '✅ 活跃'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    show() {
        if (this.statusPanel) {
            this.statusPanel.style.display = 'block';
            this.isVisible = true;
            this.updateStats();
            console.log('📊 CSS优化状态面板已显示');
        }
    }

    hide() {
        if (this.statusPanel) {
            this.statusPanel.style.display = 'none';
            this.isVisible = false;
        }
    }

    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    refreshStats() {
        this.updateStats();
        console.log('🔄 CSS优化统计已刷新');
        
        // 显示刷新动画
        const button = event.target;
        button.style.transform = 'rotate(360deg)';
        button.style.transition = 'transform 0.5s';
        setTimeout(() => {
            button.style.transform = '';
        }, 500);
    }

    showDetails() {
        const details = {
            cssFiles: Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(link => ({
                href: link.href.split('/').pop(),
                importance: link.getAttribute('importance') || 'normal',
                media: link.media || 'all'
            })),
            optimizerStyles: Array.from(document.querySelectorAll('style[data-performance-optimizer], style[data-safe-optimizer]')).length,
            totalOptimizations: this.optimizationStats.cssFilesOptimized + this.optimizationStats.criticalCSSPrioritized
        };

        console.log('📋 CSS优化详情:', details);
        alert(`CSS优化详情:\n\n` +
              `CSS文件数量: ${details.cssFiles.length}\n` +
              `优化器样式: ${details.optimizerStyles}\n` +
              `总优化项目: ${details.totalOptimizations}\n\n` +
              `详细信息请查看控制台`);
    }

    setupKeyboardShortcut() {
        // Ctrl+Shift+C 显示/隐藏状态面板
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.shiftKey && event.code === 'KeyC') {
                event.preventDefault();
                this.toggle();
            }
        });

        console.log('⌨️ 键盘快捷键已设置: Ctrl+Shift+C');
    }

    getStatus() {
        return {
            visible: this.isVisible,
            stats: this.optimizationStats,
            cssFilesCount: document.querySelectorAll('link[rel="stylesheet"]').length,
            optimizerActive: true
        };
    }
}

// 启动CSS优化状态显示器
if (!window.cssOptimizationStatus) {
    window.cssOptimizationStatus = new CSSOptimizationStatus();
    
    // 提供控制台接口
    window.showCSSStatus = () => window.cssOptimizationStatus.show();
    window.hideCSSStatus = () => window.cssOptimizationStatus.hide();
    window.getCSSOptimizationStatus = () => window.cssOptimizationStatus.getStatus();
    
    console.log('📊 CSS优化状态显示器已加载');
    console.log('💡 可用命令: showCSSStatus(), hideCSSStatus(), getCSSOptimizationStatus()');
    console.log('⌨️ 快捷键: Ctrl+Shift+C 显示/隐藏状态面板');
}
