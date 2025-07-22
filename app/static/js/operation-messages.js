/**
 * 操作提示消息配置
 * 统一管理各种操作的提示消息
 */

const OperationMessages = {
    // 通用操作
    LOADING: {
        SAVING: '正在保存数据，请稍候...',
        LOADING: '正在加载数据，请稍候...',
        DELETING: '正在删除数据，请稍候...',
        UPDATING: '正在更新数据，请稍候...',
        GENERATING: '正在生成，请稍候...',
        PROCESSING: '正在处理，请稍候...',
        UPLOADING: '正在上传文件，请稍候...',
        DOWNLOADING: '正在下载文件，请稍候...'
    },

    // 成功消息
    SUCCESS: {
        SAVE: '数据保存成功',
        UPDATE: '数据更新成功',
        DELETE: '数据删除成功',
        UPLOAD: '文件上传成功',
        DOWNLOAD: '文件下载成功',
        GENERATE: '生成成功',
        RESET: '重置成功',
        COPY: '复制成功',
        EXPORT: '导出成功',
        IMPORT: '导入成功'
    },

    // 错误消息
    ERROR: {
        SAVE: '保存失败，请重试',
        UPDATE: '更新失败，请重试',
        DELETE: '删除失败，请重试',
        UPLOAD: '文件上传失败，请重试',
        DOWNLOAD: '文件下载失败，请重试',
        NETWORK: '网络连接失败，请检查网络后重试',
        PERMISSION: '权限不足，无法执行此操作',
        VALIDATION: '数据验证失败，请检查输入',
        NOT_FOUND: '未找到相关数据',
        SERVER_ERROR: '服务器错误，请稍后重试',
        TIMEOUT: '操作超时，请重试'
    },

    // 警告消息
    WARNING: {
        UNSAVED_CHANGES: '有未保存的更改，确定要离开吗？',
        DELETE_CONFIRM: '确定要删除这条记录吗？此操作不可撤销',
        OVERWRITE_CONFIRM: '文件已存在，确定要覆盖吗？',
        LARGE_DATA: '数据量较大，处理可能需要较长时间',
        DUPLICATE_DATA: '检测到重复数据，请确认是否继续',
        INVALID_FORMAT: '数据格式不正确，请检查后重试'
    },

    // 信息消息
    INFO: {
        NO_DATA: '暂无数据',
        LOADING_DATA: '正在加载数据...',
        SELECT_ITEM: '请选择要操作的项目',
        FILL_REQUIRED: '请填写必填字段',
        CHECK_INPUT: '请检查输入内容',
        OPERATION_COMPLETE: '操作完成'
    },

    // 入库操作
    INBOUND: {
        SUCCESS: {
            SAVE: '入库记录保存成功',
            BATCH_SAVE: (count) => `成功保存 ${count} 条入库记录`,
            UPDATE: '入库记录更新成功',
            DELETE: '入库记录删除成功',
            IMPORT: (count) => `成功导入 ${count} 条入库记录`
        },
        ERROR: {
            SAVE: '入库记录保存失败',
            UPDATE: '入库记录更新失败',
            DELETE: '入库记录删除失败',
            DUPLICATE: '存在重复的入库记录',
            INVALID_DATA: '入库数据不完整或格式错误'
        },
        WARNING: {
            DELETE_CONFIRM: '确定要删除这条入库记录吗？',
            LARGE_QUANTITY: '入库数量较大，请确认是否正确'
        },
        INFO: {
            SELECT_WAREHOUSE: '请选择入库仓库',
            FILL_CUSTOMER: '请填写客户名称',
            FILL_QUANTITY: '请填写入库数量'
        }
    },

    // 出库操作
    OUTBOUND: {
        SUCCESS: {
            SAVE: '出库记录保存成功',
            BATCH_SAVE: (count) => `成功保存 ${count} 条出库记录`,
            UPDATE: '出库记录更新成功',
            DELETE: '出库记录删除成功',
            GENERATE_BATCH: (batchNo) => `批次号生成成功：${batchNo}`,
            SELECT_INVENTORY: (count) => `已选择 ${count} 条库存记录，请补充公共信息后保存`
        },
        ERROR: {
            SAVE: '出库记录保存失败',
            UPDATE: '出库记录更新失败',
            DELETE: '出库记录删除失败',
            INSUFFICIENT_STOCK: (item, available, required) => `${item} 库存不足，可用：${available}，需要：${required}`,
            INVALID_QUANTITY: '出库数量不能超过库存数量',
            NO_INVENTORY_SELECTED: '请先选择库存记录',
            BATCH_GENERATION_FAILED: '批次号生成失败'
        },
        WARNING: {
            DELETE_CONFIRM: '确定要删除这条出库记录吗？删除后库存将恢复',
            EXCEED_STOCK: (item, max) => `${item} 出库数量不能超过库存数量 ${max}`,
            NO_WEIGHT: '请输入实际出库重量'
        },
        INFO: {
            SELECT_INVENTORY: '请选择要出库的库存记录',
            FILL_COMMON_INFO: '请填写公共信息',
            GENERATE_BATCH_FIRST: '请先生成批次号'
        }
    },

    // 库存操作
    INVENTORY: {
        SUCCESS: {
            UPDATE: '库存更新成功',
            REFRESH: '库存刷新成功',
            ADJUST: '库存调整成功'
        },
        ERROR: {
            UPDATE: '库存更新失败',
            REFRESH: '库存刷新失败',
            NOT_FOUND: '未找到对应的库存记录',
            NEGATIVE_STOCK: '库存数量不能为负数'
        },
        WARNING: {
            LOW_STOCK: (item, quantity) => `${item} 库存不足，当前库存：${quantity}`,
            ZERO_STOCK: (item) => `${item} 库存为零`
        },
        INFO: {
            LOADING: '正在加载库存数据...',
            NO_STOCK: '暂无库存记录'
        }
    },

    // 文件操作
    FILE: {
        SUCCESS: {
            UPLOAD: '文件上传成功',
            DOWNLOAD: '文件下载成功',
            EXPORT: '数据导出成功',
            IMPORT: (count) => `成功导入 ${count} 条记录`
        },
        ERROR: {
            UPLOAD: '文件上传失败，请检查文件格式',
            DOWNLOAD: '文件下载失败',
            EXPORT: '数据导出失败',
            IMPORT: '数据导入失败',
            INVALID_FORMAT: '文件格式不正确，请上传Excel文件',
            FILE_TOO_LARGE: '文件过大，请选择小于10MB的文件',
            EMPTY_FILE: '文件为空，请选择有效文件'
        },
        WARNING: {
            OVERWRITE: '文件已存在，确定要覆盖吗？',
            LARGE_FILE: '文件较大，上传可能需要较长时间'
        },
        INFO: {
            SELECT_FILE: '请选择要上传的文件',
            PROCESSING: '正在处理文件...'
        }
    },

    // 用户操作
    USER: {
        SUCCESS: {
            LOGIN: '登录成功',
            LOGOUT: '退出成功',
            UPDATE_PROFILE: '个人信息更新成功',
            CHANGE_PASSWORD: '密码修改成功'
        },
        ERROR: {
            LOGIN: '登录失败，请检查用户名和密码',
            LOGOUT: '退出失败',
            UPDATE_PROFILE: '个人信息更新失败',
            CHANGE_PASSWORD: '密码修改失败',
            PERMISSION_DENIED: '权限不足，无法访问此功能',
            SESSION_EXPIRED: '会话已过期，请重新登录'
        },
        WARNING: {
            LOGOUT_CONFIRM: '确定要退出系统吗？',
            PASSWORD_WEAK: '密码强度较弱，建议使用更复杂的密码'
        },
        INFO: {
            WELCOME: (username) => `欢迎您，${username}！`,
            SESSION_TIMEOUT: '会话即将过期，请及时保存数据'
        }
    }
};

// 操作提示辅助函数
const OperationHelper = {
    /**
     * 显示操作开始提示
     * @param {string} operation - 操作类型
     * @param {string} message - 自定义消息
     */
    showStart(operation, message = null) {
        const msg = message || OperationMessages.LOADING[operation] || OperationMessages.LOADING.PROCESSING;
        return showLoading(msg);
    },

    /**
     * 显示操作成功提示
     * @param {string} category - 分类
     * @param {string} operation - 操作类型
     * @param {any} data - 额外数据
     */
    showSuccess(category, operation, data = null) {
        const messages = OperationMessages[category.toUpperCase()]?.SUCCESS;
        if (!messages) return;

        let message = messages[operation.toUpperCase()];
        if (typeof message === 'function' && data !== null) {
            message = message(data);
        }
        
        if (message) {
            showSuccess(message);
        }
    },

    /**
     * 显示操作错误提示
     * @param {string} category - 分类
     * @param {string} operation - 操作类型
     * @param {string} error - 错误信息
     */
    showError(category, operation, error = null) {
        const messages = OperationMessages[category.toUpperCase()]?.ERROR;
        let message = messages?.[operation.toUpperCase()] || OperationMessages.ERROR.SERVER_ERROR;
        
        if (error) {
            message += `：${error}`;
        }
        
        showError(message);
    },

    /**
     * 显示操作警告提示
     * @param {string} category - 分类
     * @param {string} operation - 操作类型
     * @param {any} data - 额外数据
     */
    showWarning(category, operation, data = null) {
        const messages = OperationMessages[category.toUpperCase()]?.WARNING;
        if (!messages) return;

        let message = messages[operation.toUpperCase()];
        if (typeof message === 'function' && data !== null) {
            message = message(data);
        }
        
        if (message) {
            showWarning(message);
        }
    },

    /**
     * 显示确认对话框
     * @param {string} category - 分类
     * @param {string} operation - 操作类型
     * @param {object} options - 配置选项
     */
    async showConfirm(category, operation, options = {}) {
        const messages = OperationMessages[category.toUpperCase()]?.WARNING;
        const message = messages?.[operation.toUpperCase()] || '确定要执行此操作吗？';
        
        return await showConfirm(message, {
            type: 'warning',
            ...options
        });
    }
};

// 导出到全局作用域
window.OperationMessages = OperationMessages;
window.OperationHelper = OperationHelper;
