/**
 * 原生日期时间选择器辅助脚本
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('原生日期时间选择器辅助脚本已加载');
  
  // 找到所有日期时间输入框
  const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
  
  // 为每个输入框设置当前日期时间作为默认值
  datetimeInputs.forEach(function(input) {
    if (!input.value) {
      // 获取当前日期时间，格式化为 YYYY-MM-DDThh:mm 格式
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      
      // 设置默认值
      const defaultValue = `${year}-${month}-${day}T${hours}:${minutes}`;
      input.value = defaultValue;
      
      console.log(`为 ${input.id || '未命名输入框'} 设置默认值: ${defaultValue}`);
    }
  });
}); 