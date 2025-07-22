/**
 * 性能监控面板
 * 提供实时性能监控和修复历史查看
 */

// 防止重复声明
if (typeof window.PerformanceDashboard !== 'undefined') {
    console.log('📊 性能监控面板已存在，跳过重复加载');
} else {

class PerformanceDashboard {
    constructor() {
        this.isVisible = false;
        this.updateInterval = null;
        this.init();
    }
    
    init() {
        console.log('🔧 性能监控面板开始初始化...');

        // 立即创建面板但不显示
        this.createDashboard();

        // 延迟绑定事件，确保不干扰菜单
        setTimeout(() => {
            this.bindEvents();

            // 添加快捷键 Ctrl+Shift+P 打开面板
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'P') {
                    e.preventDefault();
                    this.toggle();
                }
            });

            console.log('📊 性能监控面板已初始化 (Ctrl+Shift+P 打开) - 安全模式');
        }, 2000); // 延迟2秒绑定事件
    }
    
    createDashboard() {
        const dashboard = document.createElement('div');
        dashboard.id = 'performance-dashboard';
        dashboard.innerHTML = `
            <div class="performance-dashboard-container">
                <div class="dashboard-header">
                    <h5>🚀 性能监控面板</h5>
                    <div class="dashboard-controls">
                        <button id="refresh-performance" class="btn btn-sm btn-primary">刷新</button>
                        <button id="force-check" class="btn btn-sm btn-warning">强制检查</button>
                        <button id="close-dashboard" class="btn btn-sm btn-secondary">×</button>
                    </div>
                </div>
                
                <div class="dashboard-content">
                    <!-- 实时状态 -->
                    <div class="status-section">
                        <h6>📈 实时状态</h6>
                        <div class="status-grid">
                            <div class="status-item">
                                <span class="label">页面加载时间:</span>
                                <span id="load-time" class="value">-</span>
                            </div>
                            <div class="status-item">
                                <span class="label">内存使用:</span>
                                <span id="memory-usage" class="value">-</span>
                            </div>
                            <div class="status-item">
                                <span class="label">DOM元素数:</span>
                                <span id="dom-count" class="value">-</span>
                            </div>
                            <div class="status-item">
                                <span class="label">自动修复状态:</span>
                                <span id="auto-fix-status" class="value">-</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 性能评分 -->
                    <div class="score-section">
                        <h6>⭐ 性能评分</h6>
                        <div class="score-display">
                            <div class="score-circle">
                                <span id="performance-score">-</span>
                            </div>
                            <div class="score-details">
                                <div class="score-item">
                                    <span class="score-label">加载速度:</span>
                                    <div class="score-bar">
                                        <div id="load-speed-bar" class="score-fill"></div>
                                    </div>
                                </div>
                                <div class="score-item">
                                    <span class="score-label">响应性:</span>
                                    <div class="score-bar">
                                        <div id="responsiveness-bar" class="score-fill"></div>
                                    </div>
                                </div>
                                <div class="score-item">
                                    <span class="score-label">稳定性:</span>
                                    <div class="score-bar">
                                        <div id="stability-bar" class="score-fill"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 修复历史 -->
                    <div class="history-section">
                        <h6>🔧 修复历史</h6>
                        <div id="fix-history" class="fix-history-list">
                            <div class="no-data">暂无修复记录</div>
                        </div>
                    </div>
                    
                    <!-- 建议 -->
                    <div class="recommendations-section">
                        <h6>💡 优化建议</h6>
                        <div id="recommendations" class="recommendations-list">
                            <div class="no-data">正在分析...</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 添加样式
        const style = document.createElement('style');
        style.textContent = `
            #performance-dashboard {
                position: fixed;
                top: 20px;
                right: 20px;
                width: 400px;
                max-height: 80vh;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 12px;
                display: none;
                overflow: hidden;
            }
            
            .performance-dashboard-container {
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            
            .dashboard-header {
                background: #f8f9fa;
                padding: 12px 16px;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .dashboard-header h5 {
                margin: 0;
                font-size: 14px;
                font-weight: 600;
            }
            
            .dashboard-controls {
                display: flex;
                gap: 8px;
            }
            
            .dashboard-controls .btn {
                padding: 4px 8px;
                font-size: 11px;
                border-radius: 4px;
                border: none;
                cursor: pointer;
            }
            
            .dashboard-content {
                padding: 16px;
                overflow-y: auto;
                flex: 1;
            }
            
            .dashboard-content h6 {
                margin: 0 0 12px 0;
                font-size: 13px;
                font-weight: 600;
                color: #495057;
            }
            
            .status-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-bottom: 20px;
            }
            
            .status-item {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            
            .status-item .label {
                font-size: 11px;
                color: #6c757d;
            }
            
            .status-item .value {
                font-weight: 600;
                color: #212529;
            }
            
            .score-display {
                display: flex;
                gap: 16px;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .score-circle {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: conic-gradient(#28a745 0deg, #28a745 var(--score-deg, 0deg), #e9ecef var(--score-deg, 0deg));
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            
            .score-circle::before {
                content: '';
                position: absolute;
                width: 40px;
                height: 40px;
                background: white;
                border-radius: 50%;
            }
            
            .score-circle span {
                position: relative;
                z-index: 1;
                font-weight: 700;
                font-size: 14px;
            }
            
            .score-details {
                flex: 1;
            }
            
            .score-item {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
            }
            
            .score-label {
                width: 60px;
                font-size: 11px;
                color: #6c757d;
            }
            
            .score-bar {
                flex: 1;
                height: 6px;
                background: #e9ecef;
                border-radius: 3px;
                overflow: hidden;
            }
            
            .score-fill {
                height: 100%;
                background: #28a745;
                transition: width 0.3s ease;
            }
            
            .fix-history-list, .recommendations-list {
                max-height: 120px;
                overflow-y: auto;
            }
            
            .history-item {
                padding: 8px 12px;
                background: #f8f9fa;
                border-radius: 4px;
                margin-bottom: 8px;
                border-left: 3px solid #28a745;
            }
            
            .history-item .fix-name {
                font-weight: 600;
                color: #212529;
                font-size: 11px;
            }
            
            .history-item .fix-time {
                font-size: 10px;
                color: #6c757d;
                margin-top: 2px;
            }
            
            .recommendation-item {
                padding: 8px 12px;
                background: #fff3cd;
                border-radius: 4px;
                margin-bottom: 8px;
                border-left: 3px solid #ffc107;
                font-size: 11px;
            }
            
            .no-data {
                text-align: center;
                color: #6c757d;
                font-style: italic;
                padding: 20px;
            }
            
            /* 响应式 */
            @media (max-width: 768px) {
                #performance-dashboard {
                    width: calc(100vw - 40px);
                    right: 20px;
                    left: 20px;
                }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(dashboard);
    }
    
    bindEvents() {
        // 关闭按钮
        document.getElementById('close-dashboard').addEventListener('click', () => {
            this.hide();
        });
        
        // 刷新按钮
        document.getElementById('refresh-performance').addEventListener('click', () => {
            this.updateData();
        });
        
        // 强制检查按钮
        document.getElementById('force-check').addEventListener('click', () => {
            if (window.autoPerformanceFixer) {
                window.autoPerformanceFixer.forceCheck();
                setTimeout(() => this.updateData(), 1000);
            }
        });
        
        // 点击外部关闭
        document.addEventListener('click', (e) => {
            const dashboard = document.getElementById('performance-dashboard');
            if (this.isVisible && !dashboard.contains(e.target)) {
                this.hide();
            }
        });
    }
    
    show() {
        const dashboard = document.getElementById('performance-dashboard');
        dashboard.style.display = 'block';
        this.isVisible = true;
        
        // 开始定期更新
        this.updateData();
        this.updateInterval = setInterval(() => {
            this.updateData();
        }, 5000);
        
        console.log('📊 性能监控面板已打开');
    }
    
    hide() {
        const dashboard = document.getElementById('performance-dashboard');
        dashboard.style.display = 'none';
        this.isVisible = false;
        
        // 停止更新
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        console.log('📊 性能监控面板已关闭');
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    updateData() {
        this.updateStatus();
        this.updateScore();
        this.updateFixHistory();
        this.updateRecommendations();
    }
    
    updateStatus() {
        // 页面加载时间
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            const loadTime = navigation.loadEventEnd - navigation.fetchStart;
            document.getElementById('load-time').textContent = `${(loadTime/1000).toFixed(2)}s`;
        }
        
        // 内存使用
        if ('memory' in performance) {
            const memory = performance.memory;
            const usedMB = (memory.usedJSHeapSize / 1024 / 1024).toFixed(1);
            document.getElementById('memory-usage').textContent = `${usedMB}MB`;
        }
        
        // DOM元素数
        const domCount = document.querySelectorAll('*').length;
        document.getElementById('dom-count').textContent = domCount.toLocaleString();
        
        // 自动修复状态
        const autoFixStatus = window.autoPerformanceFixer ? 
            (window.autoPerformanceFixer.isEnabled ? '✅ 启用' : '⏸️ 禁用') : '❌ 未启动';
        document.getElementById('auto-fix-status').textContent = autoFixStatus;
    }
    
    updateScore() {
        const scores = this.calculatePerformanceScores();
        
        // 总分
        const totalScore = Math.round((scores.loadSpeed + scores.responsiveness + scores.stability) / 3);
        document.getElementById('performance-score').textContent = totalScore;
        
        // 更新圆形进度条
        const scoreCircle = document.querySelector('.score-circle');
        scoreCircle.style.setProperty('--score-deg', `${(totalScore / 100) * 360}deg`);
        
        // 更新分项评分条
        document.getElementById('load-speed-bar').style.width = `${scores.loadSpeed}%`;
        document.getElementById('responsiveness-bar').style.width = `${scores.responsiveness}%`;
        document.getElementById('stability-bar').style.width = `${scores.stability}%`;
        
        // 根据分数调整颜色
        const getColor = (score) => {
            if (score >= 80) return '#28a745';
            if (score >= 60) return '#ffc107';
            return '#dc3545';
        };
        
        document.getElementById('load-speed-bar').style.background = getColor(scores.loadSpeed);
        document.getElementById('responsiveness-bar').style.background = getColor(scores.responsiveness);
        document.getElementById('stability-bar').style.background = getColor(scores.stability);
    }
    
    calculatePerformanceScores() {
        const navigation = performance.getEntriesByType('navigation')[0];
        
        // 加载速度评分
        let loadSpeed = 100;
        if (navigation) {
            const loadTime = navigation.loadEventEnd - navigation.fetchStart;
            if (loadTime > 5000) loadSpeed = 30;
            else if (loadTime > 3000) loadSpeed = 60;
            else if (loadTime > 1000) loadSpeed = 80;
        }
        
        // 响应性评分
        let responsiveness = 100;
        const domCount = document.querySelectorAll('*').length;
        if (domCount > 3000) responsiveness = 40;
        else if (domCount > 2000) responsiveness = 70;
        else if (domCount > 1000) responsiveness = 85;
        
        // 稳定性评分
        let stability = 100;
        if ('memory' in performance) {
            const memory = performance.memory;
            const usedMB = memory.usedJSHeapSize / 1024 / 1024;
            if (usedMB > 100) stability = 50;
            else if (usedMB > 50) stability = 75;
        }
        
        return { loadSpeed, responsiveness, stability };
    }
    
    updateFixHistory() {
        const historyContainer = document.getElementById('fix-history');
        
        if (window.autoPerformanceFixer && window.autoPerformanceFixer.fixHistory.length > 0) {
            const history = window.autoPerformanceFixer.fixHistory.slice(-5).reverse();
            
            historyContainer.innerHTML = history.map(fix => `
                <div class="history-item">
                    <div class="fix-name">${fix.fix}</div>
                    <div class="fix-time">${new Date(fix.time).toLocaleTimeString()}</div>
                </div>
            `).join('');
        } else {
            historyContainer.innerHTML = '<div class="no-data">暂无修复记录</div>';
        }
    }
    
    updateRecommendations() {
        const recommendationsContainer = document.getElementById('recommendations');
        const recommendations = this.generateRecommendations();
        
        if (recommendations.length > 0) {
            recommendationsContainer.innerHTML = recommendations.map(rec => `
                <div class="recommendation-item">${rec}</div>
            `).join('');
        } else {
            recommendationsContainer.innerHTML = '<div class="no-data">性能表现良好，无需优化</div>';
        }
    }
    
    generateRecommendations() {
        const recommendations = [];
        const navigation = performance.getEntriesByType('navigation')[0];
        
        // 检查加载时间
        if (navigation) {
            const loadTime = navigation.loadEventEnd - navigation.fetchStart;
            if (loadTime > 5000) {
                recommendations.push('页面加载时间过长，建议优化资源加载');
            }
        }
        
        // 检查DOM复杂度
        const domCount = document.querySelectorAll('*').length;
        if (domCount > 2000) {
            recommendations.push('DOM元素过多，建议简化页面结构');
        }
        
        // 检查内存使用
        if ('memory' in performance) {
            const memory = performance.memory;
            const usedMB = memory.usedJSHeapSize / 1024 / 1024;
            if (usedMB > 50) {
                recommendations.push('内存使用较高，建议清理不必要的数据');
            }
        }
        
        // 检查图片优化
        const images = document.querySelectorAll('img:not([loading])');
        if (images.length > 10) {
            recommendations.push('建议为图片添加懒加载以提升性能');
        }
        
        // 检查脚本数量
        const scripts = document.querySelectorAll('script[src]');
        if (scripts.length > 20) {
            recommendations.push('脚本文件较多，建议合并或延迟加载');
        }
        
        return recommendations;
    }
}

// 全局初始化
window.PerformanceDashboard = PerformanceDashboard;

// 自动创建实例
// 立即初始化或等待DOM加载
function initPerformanceDashboard() {
    if (!window.performanceDashboard) {
        window.performanceDashboard = new PerformanceDashboard();
        console.log('🚀 性能监控面板实例已创建');
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPerformanceDashboard);
} else {
    // DOM已经加载完成，立即初始化
    initPerformanceDashboard();
}

// 导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceDashboard;
}

// 设置全局变量
window.PerformanceDashboard = PerformanceDashboard;

} // 结束重复加载保护
