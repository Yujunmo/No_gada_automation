(function () {
    var container = document.getElementById('page-sql-extractor');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">Oracle Parser</div>
            <h1>Oracle SQL 테이블 추출기</h1>
            <p>단일 SQL 쿼리 문장을 입력하면 참조하고 있는 모든 물리 테이블의 이름을 실시간으로 파싱하여 추출합니다.</p>
        </div>

        <div class="notice-box">
            <div class="notice-title">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" width="16" height="16">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                </svg>
                <span>사용 전 주의사항</span>
            </div>
            <ul class="notice-list">
                <li>이 도구는 DB에 연결하지 않고 순수 텍스트 파싱을 수행하므로, <strong>물리 테이블과 뷰(View)를 구별하지 않습니다.</strong></li>
                <li>스키마 프리픽스(<code>SCOTT.EMP</code>) 및 DB 링크(<code>EMP@DB1</code>)가 제거된 순수 테이블명만 추출됩니다. 크로스 스키마/DB 참조 여부는 SQL 원본에서 확인해 주세요.</li>
            </ul>
        </div>

        <div class="workspace">
            <div class="card input-card">
                <div class="input-group">
                    <div class="input-header">
                        <span class="input-label">Oracle SQL 입력</span>
                        <span class="input-limit">최대 1MB</span>
                    </div>
                    <textarea id="sql-extractor-input" placeholder="이곳에 Oracle SQL 쿼리를 입력하세요... (예: SELECT * FROM EMP e JOIN DEPT d ON e.id = d.id)"></textarea>
                </div>
                <div class="btn-container">
                    <button id="sql-extractor-submit">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" width="16" height="16">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                        </svg>
                        <span>테이블 추출</span>
                    </button>
                </div>
            </div>

            <div id="sql-extractor-result" class="card result-card empty">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="32" height="32" style="margin: 0 auto 12px; color: #b0aba4;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                    <p style="margin: 0; font-size: 13.5px;">왼쪽에 SQL을 입력하고 '테이블 추출' 버튼을 누르면 결과가 이곳에 표시됩니다.</p>
                </div>
            </div>
        </div>
    `;

    var sqlInput = container.querySelector('#sql-extractor-input');
    var submitBtn = container.querySelector('#sql-extractor-submit');
    var resultEl = container.querySelector('#sql-extractor-result');

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
            var res = await fetch('/extract', {
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

            var items = data.tables.map(function (t) {
                return `
                    <div class="table-item">
                        <span class="table-name" title="${t}">${t}</span>
                        <button class="copy-btn" title="복사" data-table="${t}">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"></path>
                            </svg>
                        </button>
                    </div>
                `;
            }).join('');

            resultEl.classList.remove('empty');
            resultEl.innerHTML = `
                <div class="result-header">
                    <div class="result-title">
                        <span>추출 결과</span>
                        <span class="count-badge">${data.tables.length}개</span>
                    </div>
                    <button class="btn-secondary" id="sql-extractor-copy-all" style="display: flex; align-items: center; gap: 6px;">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" width="14" height="14">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" stroke-width="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" stroke-width="2"></path>
                        </svg>
                        <span>전체 복사</span>
                    </button>
                </div>
                <div class="table-list">
                    ${items}
                </div>
            `;

            resultEl.querySelector('#sql-extractor-copy-all').addEventListener('click', function () {
                App.copyToClipboard(data.tables.join(', '), '모든 테이블명이 쉼표로 구분되어 복사되었습니다.');
            });

            resultEl.querySelectorAll('.copy-btn').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    var tableName = e.currentTarget.getAttribute('data-table');
                    App.copyToClipboard(tableName, '"' + tableName + '" 테이블명이 복사되었습니다.');
                });
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
