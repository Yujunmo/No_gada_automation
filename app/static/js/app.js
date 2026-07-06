(function () {
    const toastEl = document.getElementById('toast');

    window.App = {
        showToast: function (message) {
            toastEl.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="16" height="16" style="flex-shrink:0;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                </svg>
                <span>${message}</span>
            `;
            toastEl.classList.add('show');
            setTimeout(() => toastEl.classList.remove('show'), 2000);
        },

        copyToClipboard: async function (text, successMsg) {
            successMsg = successMsg || '클립보드에 복사되었습니다.';
            try {
                await navigator.clipboard.writeText(text);
                App.showToast(successMsg);
            } catch (err) {
                const ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                document.body.appendChild(ta);
                ta.select();
                try {
                    document.execCommand('copy');
                    App.showToast(successMsg);
                } catch (e) {
                    alert('복사에 실패했습니다. 직접 복사해 주세요.');
                }
                document.body.removeChild(ta);
            }
        }
    };

    document.querySelectorAll('.nav-item[data-page]').forEach(function (item) {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            var targetPage = item.getAttribute('data-page');

            document.querySelectorAll('.nav-item[data-page]').forEach(function (n) {
                n.classList.remove('active');
            });
            item.classList.add('active');

            document.querySelectorAll('.container[id^="page-"]').forEach(function (p) {
                p.style.display = 'none';
            });
            document.getElementById('page-' + targetPage).style.display = 'flex';
        });
    });
}());
