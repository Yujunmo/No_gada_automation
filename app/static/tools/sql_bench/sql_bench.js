(function () {
    var container = document.getElementById('page-sql-bench');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">SQL 파싱 도구</div>
            <h1>SQL Bench</h1>
            <p>Oracle SQL 자동 가공 도구. SQL을 입력하면 다양한 방식으로 가공합니다.</p>
        </div>

        <div class="workspace">
            <div class="card input-card">
                <div class="input-group">
                    <div class="input-header">
                        <span class="input-label">Oracle SQL 입력</span>
                        <span class="input-limit">최대 1MB</span>
                    </div>
                    <textarea id="sql-bench-input" placeholder="이곳에 Oracle SQL 쿼리를 입력하세요... (예: SELECT * FROM EMP e JOIN DEPT d ON e.id = d.id)"></textarea>
                </div>
                <div class="btn-container">
                    <button id="sql-bench-bind-toggle" class="btn-secondary">
                        <span>:치환</span>
                    </button>
                    <button id="sql-bench-case-toggle" class="btn-secondary">
                        <span>대문자 변환</span>
                    </button>
                    <button id="sql-bench-strip-link" class="btn-secondary">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.181 8.68a4.503 4.503 0 011.903 6.405m-9.768-2.782L3.56 14.06a4.5 4.5 0 006.364 6.365l3-3a4.5 4.5 0 00.627-5.402m4.62-9.755a4.5 4.5 0 00-6.366 6.366l.415.415M18.818 15.32A4.503 4.503 0 0117 21" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 3l18 18" />
                        </svg>
                        <span>링크 제거</span>
                    </button>
                    <button id="sql-bench-submit">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                        </svg>
                        <span>테이블 추출</span>
                    </button>
                </div>
            </div>

            <div id="sql-bench-result" class="card result-card empty">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="32" height="32" style="margin: 0 auto 12px; color: #b0aba4;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    <p style="margin: 0; font-size: 13.5px;">왼쪽에 SQL을 입력하고 '테이블 추출' 버튼을 누르면 결과가 이곳에 표시됩니다.</p>
                </div>
            </div>
        </div>
    `;

    var sqlInput = container.querySelector('#sql-bench-input');
    var submitBtn = container.querySelector('#sql-bench-submit');
    var resultEl = container.querySelector('#sql-bench-result');

    var bindToggleBtn = container.querySelector('#sql-bench-bind-toggle');
    bindToggleBtn.addEventListener('click', function () {
        var isColon = bindToggleBtn.querySelector('span').textContent === ':치환';
        sqlInput.value = isColon
            ? sqlInput.value.replace(/:[A-Za-z_][A-Za-z0-9_]*/g, function (m) { return '&' + m.slice(1); })
            : sqlInput.value.replace(/&[A-Za-z_][A-Za-z0-9_]*/g, function (m) { return ':' + m.slice(1); });
        bindToggleBtn.querySelector('span').textContent = isColon ? '&치환' : ':치환';
    });

    var caseToggleBtn = container.querySelector('#sql-bench-case-toggle');
    caseToggleBtn.addEventListener('click', function () {
        var isUpper = caseToggleBtn.querySelector('span').textContent === '대문자 변환';
        sqlInput.value = isUpper ? sqlInput.value.toUpperCase() : sqlInput.value.toLowerCase();
        caseToggleBtn.querySelector('span').textContent = isUpper ? '소문자 변환' : '대문자 변환';
    });

    container.querySelector('#sql-bench-strip-link').addEventListener('click', function () {
        var before = sqlInput.value;
        var after = before.replace(/ *@[A-Za-z0-9_$#.]+/g, '');
        if (before === after) { App.showToast('제거할 DB 링크가 없습니다.'); return; }
        sqlInput.value = after;
        App.showToast('DB 링크가 제거되었습니다.');
    });

    submitBtn.addEventListener('click', async function () {
        resultEl.classList.add('empty');
        resultEl.innerHTML = `
            <div class="empty-state">
                <svg class="spinner" viewBox="0 0 50 50">
                    <circle class="path" cx="25" cy="25" r="20" fill="none" stroke-width="5" stroke-miterlimit="10"/>
                </svg>
                <p style="margin: 12px 0 0 0; font-size: 13.5px; color: var(--text-muted);">구문 분석 및 추출 중...</p>
            </div>
        `;

        var sql = sqlInput.value;

        try {
            var res = await fetch('sql-bench/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql }),
            });

            var data = await res.json();

            if (!res.ok) {
                resultEl.classList.remove('empty');
                resultEl.innerHTML = `
                    <div class="error-box">
                        <div class="error-header">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="16" height="16">
                                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                            </svg>
                            <span>SQL 구문 분석 오류</span>
                        </div>
                        <div style="font-size: 13px; line-height: 1.6;">${data.detail}</div>
                    </div>
                `;
                return;
            }

            if (data.tables.length === 0) {
                resultEl.classList.add('empty');
                resultEl.innerHTML = `
                    <div class="empty-state">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="32" height="32" style="margin: 0 auto 12px; color: #b0aba4;">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15a4.5 4.5 0 004.5 4.5H18a3.75 3.75 0 001.332-7.257 3 3 0 00-3.758-3.848 5.25 5.25 0 00-10.233 2.33A4.502 4.502 0 002.25 15z" />
                        </svg>
                        <p style="margin: 0; font-size: 13.5px;">추출된 테이블이 없습니다.</p>
                    </div>
                `;
                return;
            }

            resultEl.classList.remove('empty');
            resultEl.innerHTML = `
                <div class="result-header">
                    <div class="result-title">
                        <span>추출 결과</span>
                        <span class="count-badge" id="sql-bench-count"></span>
                    </div>
                    <button class="btn-secondary" id="sql-bench-copy-all" style="display: flex; align-items: center; gap: 6px;">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="14" height="14">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"></path>
                        </svg>
                        <span>전체 복사</span>
                    </button>
                </div>
                <div class="result-filter">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="14" height="14">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                    </svg>
                    <input type="text" id="sql-bench-filter" placeholder="테이블 검색..." autocomplete="off">
                </div>
                <div class="table-list" id="sql-bench-list"></div>
                <div class="result-dblink">
                    <input type="text" id="sql-bench-dblink" value="@dl_patru_Trups" autocomplete="off" spellcheck="false">
                    <button id="sql-bench-link-apply">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="14" height="14">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244" />
                        </svg>
                        <span>링크 붙이기</span>
                    </button>
                </div>
            `;

            var listEl = resultEl.querySelector('#sql-bench-list');
            var countEl = resultEl.querySelector('#sql-bench-count');
            var filterEl = resultEl.querySelector('#sql-bench-filter');
            var tables = data.tables.slice();

            function renderList() {
                var q = filterEl.value.trim().toUpperCase();
                var filtered = q ? tables.filter(function (t) { return t.indexOf(q) !== -1; }) : tables;

                countEl.textContent = q
                    ? filtered.length + ' / ' + tables.length + '개'
                    : tables.length + '개';

                if (filtered.length === 0) {
                    listEl.innerHTML = '<div class="table-list-empty">일치하는 테이블이 없습니다.</div>';
                    return;
                }

                listEl.innerHTML = filtered.map(function (t) {
                    return `
                        <div class="table-item">
                            <span class="table-name" title="${t}">${t}</span>
                            <span class="sb-item-actions">
                                <button class="copy-btn" title="복사" data-table="${t}">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"></rect>
                                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"></path>
                                    </svg>
                                </button>
                                <button class="copy-btn sb-del-btn" title="삭제" data-table="${t}">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path d="M3 6h18M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2m2 0v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
                                    </svg>
                                </button>
                            </span>
                        </div>
                    `;
                }).join('');

                listEl.querySelectorAll('.copy-btn:not(.sb-del-btn)').forEach(function (btn) {
                    btn.addEventListener('click', function (e) {
                        var tableName = e.currentTarget.getAttribute('data-table');
                        App.copyToClipboard(tableName, '"' + tableName + '" 테이블명이 복사되었습니다.');
                    });
                });

                listEl.querySelectorAll('.sb-del-btn').forEach(function (btn) {
                    btn.addEventListener('click', function (e) {
                        var name = e.currentTarget.getAttribute('data-table');
                        var idx = tables.indexOf(name);
                        if (idx !== -1) tables.splice(idx, 1);
                        renderList();
                        App.showToast('"' + name + '" 삭제됨');
                    });
                });
            }

            renderList();
            filterEl.addEventListener('input', renderList);

            resultEl.querySelector('#sql-bench-copy-all').addEventListener('click', function () {
                App.copyToClipboard(tables.join(', '), '모든 테이블명이 쉼표로 구분되어 복사되었습니다.');
            });

            resultEl.querySelector('#sql-bench-link-apply').addEventListener('click', function () {
                var link = resultEl.querySelector('#sql-bench-dblink').value.trim();
                if (!link) { App.showToast('DB 링크를 입력해주세요.'); return; }
                if (link.startsWith('@')) link = link.slice(1).trim();

                var sql = sqlInput.value;
                tables.forEach(function (t) {
                    var re = new RegExp('\\b' + t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'gi');
                    sql = sql.replace(re, function (match) { return match + ' @' + link; });
                });
                sqlInput.value = sql;
                App.showToast('DB 링크가 붙여졌습니다.');
            });

        } catch (e) {
            resultEl.classList.remove('empty');
            resultEl.innerHTML = `
                <div class="error-box">
                    <div class="error-header">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                        </svg>
                        <span>서버 요청 실패</span>
                    </div>
                    <div>${e.message}</div>
                </div>
            `;
        }
    });
}());
