(function() {
  // 立即绑定所有日期时间相关的点击事件，无需等待DOMContentLoaded
  setupClicks();
  
  // 确保DOM加载完成后初始化
  document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM加载完成，设置直接点击处理器');
    setupClicks();
  });
  
  function setupClicks() {
    // 处理所有日期时间输入组的点击
    document.addEventListener('click', function(e) {
      // 查找点击的目标是否在日期选择器组内
      const target = e.target;
      
      // 处理日历图标点击
      if (target.matches('.flatpickr-trigger') || 
          target.matches('.flatpickr-trigger i') || 
          target.closest('.flatpickr-trigger')) {
        const group = target.closest('.input-group');
        if (group) {
          const input = group.querySelector('input');
          if (input) {
            console.log('日历图标被点击，尝试打开日期选择器', input.id);
            openFlatpickr(input);
          }
        }
      }
      
      // 处理输入框直接点击
      if (target.matches('input[data-datetime]') || 
          target.matches('.flatpickr-input')) {
        console.log('日期输入框被点击', target.id);
        openFlatpickr(target);
      }
    }, true);
  }
  
  // 尝试打开或初始化flatpickr
  function openFlatpickr(input) {
    if (!input) return;
    
    // 尝试使用现有实例
    if (input._flatpickr) {
      input._flatpickr.open();
      return;
    }
    
    // 检查flatpickr是否加载
    if (typeof flatpickr !== 'undefined') {
      // 基本配置
      const options = {
        enableTime: !input.hasAttribute('data-date-only'),
        noCalendar: input.hasAttribute('data-time-only'),
        dateFormat: input.hasAttribute('data-date-only') ? 'Y-m-d' : 
                  (input.hasAttribute('data-time-only') ? 'H:i' : 'Y-m-d H:i'),
        locale: 'zh',
        time_24hr: true,
        allowInput: true,
        disableMobile: false
      };
      
      // 获取所在组的配置
      const group = input.closest('[data-flatpickr]');
      if (group) {
        const enableTime = group.getAttribute('data-enable-time');
        const noCalendar = group.getAttribute('data-no-calendar');
        const dateFormat = group.getAttribute('data-date-format');
        
        if (enableTime !== null) options.enableTime = enableTime === 'true';
        if (noCalendar !== null) options.noCalendar = noCalendar === 'true';
        if (dateFormat) options.dateFormat = dateFormat;
      }
      
      // 初始化并打开
      try {
        const fp = flatpickr(input, options);
        input._flatpickr = fp;
        fp.open();
        console.log('成功初始化并打开日期选择器', input.id);
      } catch (e) {
        console.error('初始化日期选择器失败', e);
      }
    } else {
      console.log('flatpickr未加载，尝试显示原生日期选择器');
      // 尝试使用原生日期选择器
      let type = 'text';
      if (input.hasAttribute('data-date-only')) {
        type = 'date';
      } else if (input.hasAttribute('data-time-only')) {
        type = 'time'; 
      } else {
        type = 'datetime-local';
      }
      
      // 临时修改类型以使用原生选择器
      const originalType = input.type;
      input.type = type;
      input.click();
      
      // 延迟后恢复类型
      setTimeout(function() {
        input.type = originalType;
      }, 100);
    }
  }
})(); 