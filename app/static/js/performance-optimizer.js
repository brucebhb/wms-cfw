/**
 * 性能优化脚本
 * 解决页面加载卡顿问题
 */

(function() {
    'use strict';

    // 性能优化配置
    const config = {
        // 大数据表格行数阈值
        largeTableThreshold: 50,
        // 分页加载每页数量
        pageSize: 20,
        // 延迟加载时间
        lazyLoadDelay: 100,
        // 防抖延迟
        debounceDelay: 300
    };

    // 防抖函数
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // 节流函数
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // 虚拟滚动实现
    class VirtualScroll {
        constructor(container, items, itemHeight = 40) {
            this.container = container;
            this.items = items;
            this.itemHeight = itemHeight;
            this.visibleCount = Math.ceil(container.clientHeight / itemHeight) + 2;
            this.startIndex = 0;
            this.init();
        }

        init() {
            this.container.style.position = 'relative';
            this.container.style.overflow = 'auto';
            
            // 创建虚拟容器
            this.virtualContainer = document.createElement('div');
            this.virtualContainer.style.height = `${this.items.length * this.itemHeight}px`;
            this.container.appendChild(this.virtualContainer);

            // 创建可见项容器
            this.visibleContainer = document.createElement('div');
            this.visibleContainer.style.position = 'absolute';
            this.visibleContainer.style.top = '0';
            this.visibleContainer.style.width = '100%';
            this.virtualContainer.appendChild(this.visibleContainer);

            this.render();
            this.container.addEventListener('scroll', throttle(() => this.onScroll(), 16));
        }

        onScroll() {
            const scrollTop = this.container.scrollTop;
            const newStartIndex = Math.floor(scrollTop / this.itemHeight);
            
            if (newStartIndex !== this.startIndex) {
                this.startIndex = newStartIndex;
                this.render();
            }
        }

        render() {
            const endIndex = Math.min(this.startIndex + this.visibleCount, this.items.length);
            const visibleItems = this.items.slice(this.startIndex, endIndex);

            this.visibleContainer.innerHTML = '';
            this.visibleContainer.style.transform = `translateY(${this.startIndex * this.itemHeight}px)`;

            visibleItems.forEach((item, index) => {
                const element = this.createItemElement(item, this.startIndex + index);
                this.visibleContainer.appendChild(element);
            });
        }

        createItemElement(item, index) {
            const element = document.createElement('div');
            element.style.height = `${this.itemHeight}px`;
            element.innerHTML = item;
            return element;
        }
    }

    // 表格性能优化
    class TableOptimizer {
        constructor() {
            this.init();
        }

        init() {
            document.addEventListener('DOMContentLoaded', () => {
                this.optimizeTables();
            });
        }

        optimizeTables() {
            const tables = document.querySelectorAll('table.table');
            
            tables.forEach(table => {
                const tbody = table.querySelector('tbody');
                if (!tbody) return;

                const rows = tbody.querySelectorAll('tr');
                
                if (rows.length > config.largeTableThreshold) {
                    this.enablePagination(table, rows);
                }
                
                // 延迟渲染非关键内容
                this.lazyLoadTableContent(table);
            });
        }

        enablePagination(table, rows) {
            const rowsArray = Array.from(rows);
            let currentPage = 0;
            const totalPages = Math.ceil(rowsArray.length / config.pageSize);

            // 隐藏所有行
            rowsArray.forEach(row => row.style.display = 'none');

            // 创建分页控件
            const paginationContainer = document.createElement('div');
            paginationContainer.className = 'table-pagination mt-3';
            paginationContainer.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div class="pagination-info">
                        显示第 <span class="current-start">1</span> - <span class="current-end">${Math.min(config.pageSize, rowsArray.length)}</span> 条，
                        共 <span class="total-count">${rowsArray.length}</span> 条记录
                    </div>
                    <div class="pagination-controls">
                        <button class="btn btn-sm btn-outline-primary" id="prevPage" ${currentPage === 0 ? 'disabled' : ''}>
                            <i class="fas fa-chevron-left"></i> 上一页
                        </button>
                        <span class="mx-3">第 <span class="current-page">1</span> / <span class="total-pages">${totalPages}</span> 页</span>
                        <button class="btn btn-sm btn-outline-primary" id="nextPage" ${currentPage === totalPages - 1 ? 'disabled' : ''}>
                            下一页 <i class="fas fa-chevron-right"></i>
                        </button>
                    </div>
                </div>
            `;

            table.parentNode.insertBefore(paginationContainer, table.nextSibling);

            // 显示当前页
            const showPage = (page) => {
                const start = page * config.pageSize;
                const end = Math.min(start + config.pageSize, rowsArray.length);

                // 隐藏所有行
                rowsArray.forEach(row => row.style.display = 'none');

                // 显示当前页的行
                for (let i = start; i < end; i++) {
                    rowsArray[i].style.display = '';
                }

                // 更新分页信息
                paginationContainer.querySelector('.current-start').textContent = start + 1;
                paginationContainer.querySelector('.current-end').textContent = end;
                paginationContainer.querySelector('.current-page').textContent = page + 1;

                // 更新按钮状态
                const prevBtn = paginationContainer.querySelector('#prevPage');
                const nextBtn = paginationContainer.querySelector('#nextPage');
                
                prevBtn.disabled = page === 0;
                nextBtn.disabled = page === totalPages - 1;
            };

            // 绑定分页事件
            paginationContainer.querySelector('#prevPage').addEventListener('click', () => {
                if (currentPage > 0) {
                    currentPage--;
                    showPage(currentPage);
                }
            });

            paginationContainer.querySelector('#nextPage').addEventListener('click', () => {
                if (currentPage < totalPages - 1) {
                    currentPage++;
                    showPage(currentPage);
                }
            });

            // 显示第一页
            showPage(0);
        }

        lazyLoadTableContent(table) {
            const images = table.querySelectorAll('img[data-src]');
            
            if (images.length > 0) {
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            imageObserver.unobserve(img);
                        }
                    });
                });

                images.forEach(img => imageObserver.observe(img));
            }
        }
    }

    // 搜索优化
    class SearchOptimizer {
        constructor() {
            this.init();
        }

        init() {
            document.addEventListener('DOMContentLoaded', () => {
                this.optimizeSearchInputs();
            });
        }

        optimizeSearchInputs() {
            const searchInputs = document.querySelectorAll('input[type="search"], input[name*="search"], .search-input');
            
            searchInputs.forEach(input => {
                const debouncedSearch = debounce((value) => {
                    this.performSearch(input, value);
                }, config.debounceDelay);

                input.addEventListener('input', (e) => {
                    debouncedSearch(e.target.value);
                });
            });
        }

        performSearch(input, value) {
            // 实时搜索逻辑
            const table = input.closest('form')?.nextElementSibling?.querySelector('table');
            if (table && value.length > 0) {
                this.filterTableRows(table, value);
            }
        }

        filterTableRows(table, searchValue) {
            const rows = table.querySelectorAll('tbody tr');
            const searchLower = searchValue.toLowerCase();

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchLower) ? '' : 'none';
            });
        }
    }

    // 初始化所有优化器
    function initOptimizers() {
        new TableOptimizer();
        new SearchOptimizer();

        // 添加页面加载完成提示
        window.addEventListener('load', () => {
            console.log('页面性能优化已启用');
            
            // 隐藏初始加载动画
            setTimeout(() => {
                if (window.hideLoading) {
                    window.hideLoading();
                }
            }, 500);
        });
    }

    // 启动优化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOptimizers);
    } else {
        initOptimizers();
    }

})();
