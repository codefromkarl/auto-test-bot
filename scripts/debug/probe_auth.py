from playwright.sync_api import sync_playwright
import json
import os

def check_auth():
    auth_file = "scripts/auth/auth_state_real.json"
    if not os.path.exists(auth_file):
        print(f"❌ Auth file {auth_file} not found")
        return False
        
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 加载已有的登录状态
        context = browser.new_context(storage_state=auth_file)
        page = context.new_page()
        
        # 访问 AI 创作页
        url = "http://115.29.232.120/nowhi/index.html#/ai-create/index/story-list"
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")
        
        # 等待一会儿确保异步请求完成
        page.wait_for_timeout(3000)
        
        # 检查是否跳转到了登录页或出现了登录弹窗
        current_url = page.url
        print(f"Current URL: {current_url}")
        
        # 检查页面内容，通常登录后会有用户头像或特定的“剧本列表”文字
        # 我们寻找一些只有登录后才会出现的元素，或者检查是否有 424/50008 报错的 console 信息
        content = page.content()
        is_logged_in = "剧本列表" in content and "login" not in current_url.lower()
        
        # 检查是否有过期提示
        if "令牌已过期" in content or "50008" in content:
            print("❌ Found 'Token Expired' markers in page content")
            is_logged_in = False

        if is_logged_in:
            print("✅ Auth seems VALID. (Found '剧本列表' and no login redirect)")
        else:
            print("❌ Auth is INVALID or EXPIRED.")
            
        browser.close()
        return is_logged_in

if __name__ == "__main__":
    check_auth()
