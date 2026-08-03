(function () {
    var container = document.getElementById('page-table-extractor');
    if (!container) return;

    container.innerHTML = `
        <div class="header">
            <div class="badge">DBIO</div>
            <h1>Table Extractor</h1>
            <p>서비스 ID 또는 DBIO ID를 입력하면 원격지 서버에서 해당 소스를 읽어 참조하는 모든 테이블을 추출합니다.</p>
            <p style="margin-top: 8px; color: var(--text-muted);">준비 중입니다.</p>
        </div>
    `;
}());
