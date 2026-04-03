/**
 * 将技术性错误信息转换为用户友好的提示，并给出可操作建议
 */

const ERROR_MAP = [
  {
    match: /network\s*error|ERR_NETWORK|ECONNREFUSED|fetch failed/i,
    title: "网络连接异常",
    message: "当前无法连接到服务器，请检查您的网络连接。",
    suggestion: "请确认网络是否正常，或稍后再试。",
  },
  {
    match: /timeout|ETIMEDOUT|ECONNABORTED/i,
    title: "请求超时",
    message: "服务器响应时间过长。",
    suggestion: "请稍后重试，如果问题持续请联系管理员。",
  },
  {
    match: /401|unauthorized|token.*expired|jwt/i,
    title: "登录已过期",
    message: "您的登录状态已失效，需要重新登录。",
    suggestion: "请点击重新登录，然后再试一次。",
  },
  {
    match: /403|forbidden|permission|权限/i,
    title: "没有操作权限",
    message: "您当前的账号没有执行此操作的权限。",
    suggestion: "如需此权限，请联系管理员开通。",
  },
  {
    match: /404|not\s*found|未找到/i,
    title: "未找到相关数据",
    message: "请求的资源不存在或已被删除。",
    suggestion: "请检查访问地址是否正确，或返回上一页重试。",
  },
  {
    match: /409|conflict|已存在|duplicate|unique/i,
    title: "数据冲突",
    message: "提交的数据与已有记录冲突。",
    suggestion: "请检查是否有重复的编码或名称，修改后再提交。",
  },
  {
    match: /422|validation|验证失败|invalid/i,
    title: "信息填写有误",
    message: "提交的表单信息不完整或格式不正确。",
    suggestion: "请检查标红的字段，修正后再提交。",
  },
  {
    match: /429|too\s*many\s*requests|rate\s*limit/i,
    title: "操作过于频繁",
    message: "短时间内请求次数过多。",
    suggestion: "请稍等片刻后再试。",
  },
  {
    match: /500|internal\s*server/i,
    title: "服务器异常",
    message: "服务器处理请求时遇到问题。",
    suggestion: "请稍后重试，如果问题持续请联系技术支持。",
  },
  {
    match: /502|bad\s*gateway|503|service\s*unavailable/i,
    title: "服务暂时不可用",
    message: "服务器正在维护或暂时无法提供服务。",
    suggestion: "请稍后再试。",
  },
];

/**
 * 将错误对象转换为用户友好信息
 * @param {Error|Object} error - 原始错误对象
 * @returns {{ title: string, message: string, suggestion: string }}
 */
export function getFriendlyError(error) {
  if (!error) {
    return {
      title: "操作失败",
      message: "发生了未知错误。",
      suggestion: "请稍后重试，如果问题持续请联系管理员。",
    };
  }

  const statusCode = error?.response?.status;
  const rawMessage =
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    String(error);

  // Build a string to match against
  const matchStr = `${statusCode || ""} ${rawMessage}`;

  for (const rule of ERROR_MAP) {
    if (rule.match.test(matchStr)) {
      return {
        title: rule.title,
        message: rule.message,
        suggestion: rule.suggestion,
      };
    }
  }

  return {
    title: "操作失败",
    message: "请求未能成功完成。",
    suggestion: "请稍后重试，如果问题持续请联系管理员。",
  };
}

/**
 * 获取简短的友好错误提示文本（用于 toast）
 * @param {Error|Object} error
 * @returns {string}
 */
export function getFriendlyErrorMessage(error) {
  const { message, suggestion } = getFriendlyError(error);
  return `${message} ${suggestion}`;
}
