/**
 * 轻量级脚本加载器 - 用于首页和不需要表格的页面
 * 避免加载不必要的重型组件，提高页面性能
 */
(function() {
    'use strict';
    
    console.log('[轻量加载器] 初始化页面');
    console.time('页面初始化');
    
    // 获取当前页面路径
    const currentPath = window.location.pathname;
    
    // 工具函数
    const util = {
        // 简化的DOM选择器
        $(selector) {
            return document.querySelector(selector);
        },
        
        // 添加事件监听器
        on(element, event, handler) {
            if (element) {
                element.addEventListener(event, handler);
            }
        },
        
        // 延迟执行
        delay(callback, ms = 10) {
            return setTimeout(callback, ms);
        }
    };
    
    // 初始化侧边栏交互
    function initSidebar() {
        // 侧边栏切换
        const sidebarToggler = util.$('#sidebar-toggler');
        util.on(sidebarToggler, 'click', function(e) {
            e.preventDefault();
            const sidebar = util.$('#sidebar');
            const content = util.$('#content');
            
            if (sidebar) {
                sidebar.classList.toggle('active');
                
                if (content) {
                    content.classList.toggle('active');
                }
                
                // 更新图标
                const icon = this.querySelector('i');
                if (icon) {
                    if (sidebar.classList.contains('active')) {
                        icon.classList.remove('fa-angle-left');
                        icon.classList.add('fa-angle-right');
                        localStorage.setItem('sidebarState', 'collapsed');
                    } else {
                        icon.classList.remove('fa-angle-right');
                        icon.classList.add('fa-angle-left');
                        localStorage.setItem('sidebarState', 'expanded');
                    }
                }
            }
        });
    }
    
    // 初始化页面动画和过渡效果
    function initPageEffects() {
        // 添加进入页面的淡入效果
        const mainContent = util.$('.main-content');
        if (mainContent) {
            mainContent.style.opacity = '0';
            util.delay(() => {
                mainContent.style.transition = 'opacity 0.3s ease';
                mainContent.style.opacity = '1';
            }, 10);
        }
    }
    
    // 根据页面类型进行特定初始化
    function initPageSpecific() {
        // 首页特定初始化
        if (currentPath === '/' || currentPath.endsWith('index')) {
            console.log('[轻量加载器] 检测到首页，应用首页特定优化');
            
            // 首页卡片鼠标悬停效果
            const cardHoverEffect = () => {
                const cards = document.querySelectorAll('.card');
                cards.forEach(card => {
                    card.addEventListener('mouseenter', () => {
                        card.style.transform = 'translateY(-5px)';
                        card.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
                    });
                    
                    card.addEventListener('mouseleave', () => {
                        card.style.transform = 'translateY(0)';
                        card.style.boxShadow = '0 5px 10px rgba(0,0,0,0.05)';
                    });
                });
            };
            
            util.delay(cardHoverEffect, 100);
        }
        
        // 列表页特定初始化
        if (currentPath.includes('list')) {
            console.log('[轻量加载器] 检测到列表页面，应用列表页特定优化');
            
            // 列表页搜索框聚焦效果
            const searchInput = util.$('.search-box input');
            if (searchInput) {
                searchInput.addEventListener('focus', () => {
                    searchInput.parentElement.style.boxShadow = '0 0 0 0.25rem rgba(13, 110, 253, 0.25)';
                });
                
                searchInput.addEventListener('blur', () => {
                    searchInput.parentElement.style.boxShadow = '';
                });
            }
        }
    }
    
    // 主初始化函数
    function initialize() {
        // 应用常规初始化
        initSidebar();
        initPageEffects();
        initPageSpecific();
        
        console.timeEnd('页面初始化');
        console.log('[轻量加载器] 页面初始化完成');
    }
    
    // 当DOM内容加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // 如果DOM已加载完成，直接初始化
        initialize();
    }
})(); 