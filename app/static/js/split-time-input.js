/**
 * 拆分时间输入处理脚本
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('拆分时间输入处理脚本已加载 - 修复版');
  
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
  
  // 处理小时输入框
  const hourInputs = document.querySelectorAll('.split-time-hour');
  hourInputs.forEach(function(input) {
    // 设置当前小时为默认值
    if (!input.value) {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      
      input.value = hours;
      console.log(`为 ${input.id || '未命名小时输入框'} 设置默认值: ${hours}`);
    } else if (input.value.length === 1) {
      input.value = input.value.padStart(2, '0');
      console.log(`补全 ${input.id || '未命名小时输入框'} 的值: ${input.value}`);
    }
    
    // 只允许输入数字
    input.addEventListener('keypress', function(e) {
      if (!/^\d$/.test(e.key)) {
        e.preventDefault();
      }
    });
    
    // 输入时验证
    input.addEventListener('input', function() {
      console.log(`小时输入: ${this.id} => ${this.value}`);
      
      // 允许输入两位数字
      if (this.value.length > 2) {
        this.value = this.value.substring(0, 2);
      }
      
      // 如果输入了2位数字，自动跳到分钟输入框
      if (this.value.length === 2) {
        const baseId = this.id.replace('-hour', '');
        const minuteInput = document.getElementById(baseId + '-minute');
        if (minuteInput) {
          minuteInput.focus();
          minuteInput.select();
        }
      }
      
      validateHour(this);
      combineDateTime(this);
    });
    
    // 失去焦点时格式化
    input.addEventListener('blur', function() {
      if (this.value) {
        formatHour(this);
        validateHour(this);
        combineDateTime(this);
      }
    });
  });
  
  // 处理分钟输入框
  const minuteInputs = document.querySelectorAll('.split-time-minute');
  minuteInputs.forEach(function(input) {
    // 设置当前分钟为默认值
    if (!input.value) {
      const now = new Date();
      const minutes = String(now.getMinutes()).padStart(2, '0');
      
      input.value = minutes;
      console.log(`为 ${input.id || '未命名分钟输入框'} 设置默认值: ${minutes}`);
    } else if (input.value.length === 1) {
      input.value = input.value.padStart(2, '0');
      console.log(`补全 ${input.id || '未命名分钟输入框'} 的值: ${input.value}`);
    }
    
    // 只允许输入数字
    input.addEventListener('keypress', function(e) {
      if (!/^\d$/.test(e.key)) {
        e.preventDefault();
      }
    });
    
    // 输入时验证
    input.addEventListener('input', function() {
      console.log(`分钟输入: ${this.id} => ${this.value}`);
      
      // 允许输入两位数字
      if (this.value.length > 2) {
        this.value = this.value.substring(0, 2);
      }
      
      validateMinute(this);
      combineDateTime(this);
    });
    
    // 失去焦点时格式化
    input.addEventListener('blur', function() {
      if (this.value) {
        formatMinute(this);
        validateMinute(this);
        combineDateTime(this);
      }
    });
  });
  
  // 日期变更时更新隐藏字段
  dateInputs.forEach(function(dateInput) {
    dateInput.addEventListener('change', function() {
      const baseId = dateInput.id.replace('-date', '');
      combineDateTime(this, baseId);
    });
  });
  
  // 初始化所有隐藏字段
  hourInputs.forEach(function(hourInput) {
    combineDateTime(hourInput);
  });
  
  // 表单提交前验证
  const forms = document.querySelectorAll('form');
  forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      const hourInputs = form.querySelectorAll('.split-time-hour');
      const minuteInputs = form.querySelectorAll('.split-time-minute');
      let isValid = true;
      
      // 验证小时
      hourInputs.forEach(function(input) {
        formatHour(input);
        if (!validateHour(input)) {
          isValid = false;
        }
        combineDateTime(input);
      });
      
      // 验证分钟
      minuteInputs.forEach(function(input) {
        formatMinute(input);
        if (!validateMinute(input)) {
          isValid = false;
        }
      });
      
      if (!isValid) {
        e.preventDefault();
        alert('请检查时间格式是否正确（小时: 0-23, 分钟: 0-59）');
      }
    });
  });
  
  console.log('拆分时间输入处理脚本初始化完成');
});

/**
 * 格式化小时输入
 */
function formatHour(input) {
  let value = input.value.trim();
  
  // 如果为空，设置为00
  if (!value) {
    input.value = '00';
    return;
  }
  
  // 只保留数字
  value = value.replace(/\D/g, '');
  
  // 确保是两位数
  if (value.length === 1) {
    value = '0' + value;
  } else if (value.length > 2) {
    value = value.substring(0, 2);
  }
  
  // 验证范围
  let hours = parseInt(value, 10);
  if (isNaN(hours) || hours > 23) {
    hours = hours > 23 ? 23 : 0;
  }
  
  // 设置格式化后的值
  input.value = String(hours).padStart(2, '0');
  console.log(`格式化小时: ${input.id} => ${input.value}`);
}

/**
 * 验证小时输入
 */
function validateHour(input) {
  const value = input.value.trim();
  const hourRegex = /^([0-1]?[0-9]|2[0-3])$/;
  const isValid = hourRegex.test(value);
  
  // 移除验证样式类，不要添加绿色对勾
  input.classList.remove('is-invalid');
  input.classList.remove('is-valid');
  
  return isValid;
}

/**
 * 格式化分钟输入
 */
function formatMinute(input) {
  let value = input.value.trim();
  
  // 如果为空，设置为00
  if (!value) {
    input.value = '00';
    return;
  }
  
  // 只保留数字
  value = value.replace(/\D/g, '');
  
  // 确保是两位数
  if (value.length === 1) {
    value = '0' + value;
  } else if (value.length > 2) {
    value = value.substring(0, 2);
  }
  
  // 验证范围
  let minutes = parseInt(value, 10);
  if (isNaN(minutes) || minutes > 59) {
    minutes = minutes > 59 ? 59 : 0;
  }
  
  // 设置格式化后的值
  input.value = String(minutes).padStart(2, '0');
  console.log(`格式化分钟: ${input.id} => ${input.value}`);
}

/**
 * 验证分钟输入
 */
function validateMinute(input) {
  const value = input.value.trim();
  const minuteRegex = /^[0-5]?[0-9]$/;
  const isValid = minuteRegex.test(value);
  
  // 移除验证样式类，不要添加绿色对勾
  input.classList.remove('is-invalid');
  input.classList.remove('is-valid');
  
  return isValid;
}

/**
 * 合并日期和时间到隐藏字段
 */
function combineDateTime(input, providedBaseId) {
  // 从输入框获取基础ID，支持日期、小时、分钟输入框
  const inputId = input.id;
  const baseId = providedBaseId || 
                 (inputId.endsWith('-hour') ? inputId.replace('-hour', '') :
                 (inputId.endsWith('-minute') ? inputId.replace('-minute', '') :
                 (inputId.endsWith('-date') ? inputId.replace('-date', '') : null)));
  
  if (!baseId) {
    console.error('无法确定基础ID:', inputId);
    return;
  }
  
  // 获取相关元素
  const dateInput = document.getElementById(baseId + '-date');
  const hourInput = document.getElementById(baseId + '-hour');
  const minuteInput = document.getElementById(baseId + '-minute');
  const hiddenInput = document.getElementById(baseId);
  
  if (dateInput && hourInput && minuteInput && hiddenInput) {
    const dateValue = dateInput.value;
    const hourValue = hourInput.value || '00';
    const minuteValue = minuteInput.value || '00';
    
    if (dateValue) {
      // 即使时间字段为空也设置一个默认值确保日期可以保存
      hiddenInput.value = `${dateValue} ${hourValue}:${minuteValue}`;
      console.log(`合并日期时间 ${baseId}: ${hiddenInput.value}`);
    }
  } else {
    console.warn(`无法找到所有必需的输入元素。baseId: ${baseId}`);
    if (!dateInput) console.warn(`未找到: ${baseId}-date`);
    if (!hourInput) console.warn(`未找到: ${baseId}-hour`);
    if (!minuteInput) console.warn(`未找到: ${baseId}-minute`);
    if (!hiddenInput) console.warn(`未找到: ${baseId}`);
  }
} 