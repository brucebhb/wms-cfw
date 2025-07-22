
// 通用工具函数
function showAlert(message, type = 'info') {
    // 显示提示信息
    console.log(`[${type.toUpperCase()}] ${message}`);
}

function formatDate(date) {
    // 格式化日期
    if (!date) return '';
    return new Date(date).toLocaleDateString('zh-CN');
}

function formatNumber(num) {
    // 格式化数字
    if (num === null || num === undefined || num === '') return '';
    return Number(num).toLocaleString();
}

// 页面加载优化
document.addEventListener('DOMContentLoaded', function() {
    // 延迟加载非关键内容
    setTimeout(function() {
        // 这里可以放置非关键的初始化代码
    }, 100);
});
