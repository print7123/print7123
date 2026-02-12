// 새로운 깔끔한 견적서 미리보기 함수
function showCleanPreview() {
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email').value,
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };

    // 가격 계산
    fetch('/calculate_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(priceInfo => {
        // 새로운 깔끔한 모달 HTML
        const modalHtml = `
        <div class="modal fade" id="cleanPreviewModal" tabindex="-1" aria-labelledby="cleanPreviewModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="cleanPreviewModalLabel">
                            <i class="fas fa-eye me-2"></i>견적서 미리보기
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" style="padding: 20px; background: #f8f9fa;">
                        <div class="page a4" style="width: 100%; max-width: 600px; margin: 0 auto; font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif; color: #000; padding: 0; display: block;">
                            <!-- 가격 안내 -->
                            <div style="background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 15px; font-size: 12px; color: #6c757d;">
                                <i class="fas fa-info-circle me-2"></i>가격 안내: 페이지 수와 수량에 따라 차등 가격이 적용됩니다. 기본 80g 복사용지, 부가세 포함입니다.
                            </div>
                            
                            <!-- 견적서 상자 -->
                            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                                <h2 style="color: #155724; font-size: 18px; font-weight: bold; margin-bottom: 15px;">
                                    <i class="fas fa-check-circle me-2"></i>견적서
                                </h2>
                                
                                <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                                    <!-- 좌측 상세 정보 -->
                                    <div style="flex: 1;">
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>수신인:</strong> ${formData.customerName || '1'}
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>견적일자:</strong> ${new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>총 페이지 수:</strong> ${priceInfo.total_pages}페이지
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>페이지당 단가:</strong> ${priceInfo.unit_print_price}원
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>총 출력 가격:</strong> ${priceInfo.print_price.toLocaleString()}원
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>제본 가격:</strong> ${priceInfo.binding_price.toLocaleString()}원
                                        </div>
                                    </div>
                                    
                                    <!-- 우측 요약 정보 -->
                                    <div style="flex: 1;">
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>상품명:</strong> ${getProductName(formData)}
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>규격:</strong> ${formData.size || 'A4'}
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>단가 (출력+제본):</strong> ${priceInfo.unit_price.toLocaleString()}원
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 13px;">
                                            <strong>수량:</strong> ${parseInt(formData.quantity).toLocaleString()}권
                                        </div>
                                        <div style="margin-bottom: 8px; font-size: 16px; font-weight: bold; color: #007bff;">
                                            <strong>총 가격:</strong> ${priceInfo.total_price.toLocaleString()}원
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- 공급자 정보 -->
                                <div style="background: #fff; border-radius: 5px; padding: 15px; margin-top: 15px;">
                                    <h4 style="color: #155724; font-size: 14px; margin-bottom: 10px;">공급자 정보</h4>
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 11px;">
                                        <div><strong>상호:</strong> 온누리인쇄나라</div>
                                        <div><strong>사업자번호:</strong> 491-20-00640</div>
                                        <div><strong>대표자:</strong> 류도현</div>
                                        <div><strong>전화번호:</strong> 02-6338-7123</div>
                                        <div><strong>주소:</strong> 서울 금천구 가산디지털1로 142 가산더스카이밸리1차 8층 816호</div>
                                        <div><strong>계좌번호:</strong> 신한 110-493-223413</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-2"></i>닫기
                        </button>
                        <button type="button" class="btn btn-primary" onclick="printCleanPreview()">
                            <i class="fas fa-print me-2"></i>인쇄 (PDF 저장)
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        // 기존 모달 제거
        const existingModal = document.getElementById('cleanPreviewModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // 새 모달 추가
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 모달 표시
        const modal = new bootstrap.Modal(document.getElementById('cleanPreviewModal'));
        modal.show();
    })
    .catch(error => {
        console.error('가격 계산 오류:', error);
        showAlert('가격 계산 중 오류가 발생했습니다.', 'danger');
    });
}

// 깔끔한 견적서 인쇄 함수
function printCleanPreview() {
    const modal = document.getElementById('cleanPreviewModal');
    const modalBody = modal.querySelector('.modal-body');
    
    if (!modalBody) {
        showAlert('미리보기 데이터를 찾을 수 없습니다.', 'danger');
        return;
    }
    
    // 저장 경로 안내 메시지
    const saveMessage = `
        📁 PDF 저장 안내
        
        인쇄 대화상자가 열리면:
        1. "대상"을 "PDF로 저장" 선택
        2. 파일명을 "견적서_${new Date().toISOString().slice(0,10)}.pdf"로 설정
        3. 원하는 폴더에 저장
        
        💡 팁: 바탕화면이나 문서 폴더에 저장하시면 쉽게 찾을 수 있습니다.
    `;
    
    // 안내 메시지 표시
    showAlert(saveMessage, 'info');
    
    // 2초 후 인쇄 창 열기
    setTimeout(() => {
        // 새 창 열기
        const printWindow = window.open('', '_blank');
        
        // 인쇄용 HTML 생성
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>견적서</title>
                <style>
                    @page {
                        size: A4;
                        margin: 10mm;
                    }
                    body {
                        font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        font-size: 12px;
                        line-height: 1.4;
                    }
                    .page {
                        width: 100%;
                        max-width: 180mm;
                        margin: 0 auto;
                    }
                    .info-box {
                        background: #e9ecef;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 15px;
                        font-size: 12px;
                        color: #6c757d;
                    }
                    .quote-box {
                        background: #d4edda;
                        border: 1px solid #c3e6cb;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 15px;
                    }
                    .quote-title {
                        color: #155724;
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 15px;
                    }
                    .info-grid {
                        display: flex;
                        gap: 20px;
                        margin-bottom: 15px;
                    }
                    .info-left, .info-right {
                        flex: 1;
                    }
                    .info-item {
                        margin-bottom: 8px;
                        font-size: 13px;
                    }
                    .total-price {
                        font-size: 16px;
                        font-weight: bold;
                        color: #007bff;
                    }
                    .supplier-info {
                        background: #fff;
                        border-radius: 5px;
                        padding: 15px;
                        margin-top: 15px;
                    }
                    .supplier-title {
                        color: #155724;
                        font-size: 14px;
                        margin-bottom: 10px;
                    }
                    .supplier-grid {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 10px;
                        font-size: 11px;
                    }
                </style>
            </head>
            <body>
                ${modalBody.innerHTML}
            </body>
            </html>
        `;
        
        printWindow.document.write(printContent);
        printWindow.document.close();
        
        // 인쇄 대화상자 열기
        printWindow.onload = function() {
            printWindow.print();
            printWindow.close();
        };
    }, 2000);
}
