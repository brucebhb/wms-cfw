/**
 * 带固定冒号的时间输入处理脚本
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('带固定冒号的时间输入处理脚本已加载');
  
  // 设置当前日期为默认值
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(function(input) {
    if (!input.value) {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      
      const defaultValue = `${year}-${month}-${day}`;
      input.value = defaultValue;
      
      console.log(`为 ${input.id || '未命名日期输入框'} 设置默认值: ${defaultValue}`);
    }
  });
  
  // 处理时间输入框
  const timeInputs = document.querySelectorAll('.fixed-colon-input');
  timeInputs.forEach(function(input) {
    // 设置当前时间为默认值
    if (!input.value) {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      
      const defaultValue = `${hours} ${minutes}`;
      input.value = defaultValue;
      
      console.log(`为 ${input.id || '未命名时间输入框'} 设置默认值: ${defaultValue}`);
    }
    
    // 监听输入事件，限制只能输入数字
    input.addEventListener('keypress', function(e) {
      const key = e.key;
      // 只允许输入数字
      if (!/^\d$/.test(key)) {
        e.preventDefault();
      }
      
      // 如果已经输入了4个数字，阻止继续输入
      if (this.value.replace(/\s/g, '').length >= 4) {
        e.preventDefault();
      }
    });
    
    // 监听输入事件
    input.addEventListener('input', function(e) {
      formatFixedColonTime(this);
      validateFixedColonTime(this);
    });
    
    // 失去焦点时格式化
    input.addEventListener('blur', function(e) {
      formatFixedColonTime(this, true);
      validateFixedColonTime(this);
      combineDateTime(this);
    });
    
    // 初始验证
    formatFixedColonTime(input);
    validateFixedColonTime(input);
  });
  
  // 日期变更时更新隐藏字段
  dateInputs.forEach(function(dateInput) {
    dateInput.addEventListener('change', function() {
      const baseId = dateInput.id.replace('-date', '');
      const timeInput = document.getElementById(baseId + '-time');
      if (timeInput) {
        combineDateTime(timeInput);
      }
    });
  });
  
  // 初始化所有隐藏字段
  timeInputs.forEach(function(timeInput) {
    combineDateTime(timeInput);
  });
  
  // 表单提交前验证
  const forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      const timeInputs = form.querySelectorAll('.fixed-colon-input');
      let isValid = true;
      
      timeInputs.forEach(function(input) {
        if (!validateFixedColonTime(input)) {
          isValid = false;
        }
        combineDateTime(input);
      });
      
      if (!isValid) {
        e.preventDefault();
        alert('请检查时间格式是否正确（HH:MM，24小时制）');
      }
    });
  });
});

/**
 * 格式化带固定冒号的时间输入
 * @param {HTMLInputElement} input - 时间输入框元素
 * @param {boolean} complete - 是否在失去焦点时完成格式化
 */
function formatFixedColonTime(input, complete = false) {
  // 获取纯数字
  let digits = input.value.replace(/\D/g, '');
  
  // 如果为空，设置当前时间
  if (!digits && complete) {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    input.value = `${hours} ${minutes}`;
    return;
  }
  
  // 限制最多4个数字
  digits = digits.substring(0, 4);
  
  // 根据数字长度进行格式化
  switch (digits.length) {
    case 0:
      input.value = '';
      break;
    case 1:
      input.value = digits + '   ';
      break;
    case 2:
      input.value = digits + '   ';
      break;
    case 3:
      input.value = digits.substring(0, 2) + ' ' + digits.substring(2) + ' ';
      break;
    case 4:
      input.value = digits.substring(0, 2) + ' ' + digits.substring(2, 4);
      break;
  }
  
  // 如果是完成格式化，验证并修正值
  if (complete && digits.length > 0) {
    // 确保至少有4位数字
    while (digits.length < 4) {
      digits += '0';
    }
    
    let hours = parseInt(digits.substring(0, 2), 10);
    let minutes = parseInt(digits.substring(2, 4), 10);
    
    // 修正无效值
    if (hours > 23) hours = 23;
    if (minutes > 59) minutes = 59;
    
    // 重新格式化
    input.value = String(hours).padStart(2, '0') + ' ' + String(minutes).padStart(2, '0');
  }
}

/**
 * 验证时间格式
 */
function validateFixedColonTime(input) {
  // 获取纯数字
  const digits = input.value.replace(/\D/g, '');
  
  // 如果为空，不验证
  if (digits.length === 0) {
    input.classList.remove('is-valid', 'is-invalid');
    return false;
  }
  
  // 检查是否有足够的数字
  if (digits.length < 4) {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
    return false;
  }
  
  // 验证小时和分钟
  const hours = parseInt(digits.substring(0, 2), 10);
  const minutes = parseInt(digits.substring(2, 4), 10);
  
  const isValid = hours >= 0 && hours <= 23 && minutes >= 0 && minutes <= 59;
  
  if (isValid) {
    input.classList.remove('is-invalid');
    input.classList.add('is-valid');
  } else {
    input.classList.remove('is-valid');
    input.classList.add('is-invalid');
  }
  
  return isValid;
}

/**
 * 合并日期和时间到隐藏字段
 */
function combineDateTime(timeInput) {
  const baseId = timeInput.id.replace('-time', '');
  const dateInput = document.getElementById(baseId + '-date');
  const hiddenInput = document.getElementById(baseId);
  
  if (dateInput && hiddenInput) {
    const dateValue = dateInput.value;
    // 获取纯数字
    const digits = timeInput.value.replace(/\D/g, '');
    
    if (dateValue && digits.length === 4) {
      // 格式化为HH:MM
      const hours = digits.substring(0, 2);
      const minutes = digits.substring(2, 4);
      const formattedTime = `${hours}:${minutes}`;
      
      hiddenInput.value = `${dateValue} ${formattedTime}`;
      console.log(`合并日期时间: ${hiddenInput.value}`);
    }
  }
} 