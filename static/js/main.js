// 온누리인쇄나라 전용 JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 견적 계산 폼 처리
    const quoteForm = document.getElementById('quoteForm');
    if (quoteForm) {
        quoteForm.addEventListener('submit', handleQuoteCalculation);
    }
    
    // 스크롤 애니메이션
    initScrollAnimations();
    
    // 부드러운 스크롤
    initSmoothScroll();
});

// 견적 계산 처리 (버튼 클릭 이벤트용)
function handleQuoteCalculation(e) {
    if (e) {
        e.preventDefault();
    }
    
    // 계산 중 플래그 설정 (값 변경 허용)
    window.isCalculating = true;
    
    console.log('견적 계산 함수 시작');
    
    // 폼 데이터 수집
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email') ? document.getElementById('email').value : '',
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };
    
    console.log('폼 데이터:', formData);
    
    // 필수 필드 검증
    if (!formData.customerName || !formData.pages || !formData.printType || !formData.bindingType || !formData.quantity) {
        showAlert('모든 필수 항목을 입력해주세요.', 'warning');
        return;
    }
    
    // 로딩 표시
    const calculateBtn = document.getElementById('calculateBtn');
    if (!calculateBtn) {
        console.error('calculateBtn 요소를 찾을 수 없습니다');
        showAlert('견적 계산 버튼을 찾을 수 없습니다.', 'danger');
        return;
    }
    
    const originalText = calculateBtn.innerHTML;
    calculateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>견적 계산 중...';
    calculateBtn.disabled = true;
    
    console.log('견적 계산 요청 시작');
    
    // 견적 계산 API 호출
    fetch('/quote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('견적 계산 응답 상태:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('견적 계산 응답 데이터:', data);
        displayQuoteResult(data, formData);
    })
    .catch(error => {
        console.error('견적 계산 오류:', error);
        showAlert('견적 계산 중 오류가 발생했습니다: ' + error.message, 'danger');
    })
    .finally(() => {
        // 버튼 상태 복원
        calculateBtn.innerHTML = originalText;
        calculateBtn.disabled = false;
        // 계산 완료 후 플래그 해제
        window.isCalculating = false;
        console.log('견적 계산 함수 완료');
    });
}

// 견적 결과 표시
function displayQuoteResult(data, formData) {
    const resultDiv = document.getElementById('quoteResult');
    
    if (!resultDiv) {
        console.error('quoteResult 요소를 찾을 수 없습니다');
        showAlert('견적 결과를 표시할 영역을 찾을 수 없습니다.', 'danger');
        return;
    }
    
    console.log('견적 결과 표시 시작:', data);
    
    // 결과 데이터 설정
    const unitPrintPriceEl = document.getElementById('unitPrintPrice');
    const printPriceEl = document.getElementById('printPrice');
    const bindingPriceEl = document.getElementById('bindingPrice');
    const totalBindingPriceEl = document.getElementById('totalBindingPrice');
    const unitPriceEl = document.getElementById('unitPrice');
    const quantityResultEl = document.getElementById('quantityResult');
    const totalPriceEl = document.getElementById('totalPrice');
    
    if (unitPrintPriceEl) unitPrintPriceEl.textContent = data.unit_print_price.toLocaleString();
    if (printPriceEl) printPriceEl.textContent = data.print_price.toLocaleString();
    if (bindingPriceEl) bindingPriceEl.textContent = data.unit_binding_price.toLocaleString();
    
    // 총 제본 비용 표시 (서버에서 이미 총 비용으로 계산됨)
    if (totalBindingPriceEl) totalBindingPriceEl.textContent = data.binding_price.toLocaleString();
    
    if (unitPriceEl) unitPriceEl.textContent = data.unit_price.toLocaleString();
    if (quantityResultEl) quantityResultEl.textContent = formData.quantity;
    // 총 가격 표시 (부가세 포함된 금액)
    if (totalPriceEl) totalPriceEl.textContent = data.total_price_with_tax.toLocaleString();
    
    // 총 페이지 수 표시
    if (data.total_pages) {
        const totalPagesElement = document.getElementById('totalPages');
        if (totalPagesElement) {
            totalPagesElement.textContent = data.total_pages.toLocaleString();
        }
    }
    
    // 잉크칼라 선택 시 특별 안내 메시지
    if (formData.printType === 'ink_color') {
        const inkColorInfo = document.getElementById('inkColorInfo');
        if (inkColorInfo) {
            inkColorInfo.style.display = 'block';
        }
    } else {
        const inkColorInfo = document.getElementById('inkColorInfo');
        if (inkColorInfo) {
            inkColorInfo.style.display = 'none';
        }
    }
    
    // 결과 표시
    resultDiv.style.display = 'block';
    resultDiv.scrollIntoView({ behavior: 'smooth' });
    
    // PDF 버튼 표시
    
    // 결제 버튼 표시
    const paymentBtn = document.getElementById('paymentBtn');
    if (paymentBtn) {
        paymentBtn.style.display = 'inline-block';
    }
    
    // 성공 알림
    showAlert('견적이 계산되었습니다!', 'success');
    
    // 계산 완료 후 원본 값으로 복원 (보호 모드)
    if (typeof isFormProtected !== 'undefined' && isFormProtected) {
        setTimeout(() => {
            const quoteForm = document.getElementById('quoteForm');
            if (quoteForm) {
                const inputs = quoteForm.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    if (input.getAttribute('data-protected') === 'true') {
                        const originalValue = input.getAttribute('data-original-value');
                        if (input.value !== originalValue) {
                            input.value = originalValue;
                            input.setAttribute('value', originalValue);
                        }
                    }
                });
            }
            window.isCalculating = false;
        }, 1000);
    } else {
        window.isCalculating = false;
    }
}

    
    const naverShoppingUrl = `https://smartstore.naver.com/print7123/products/자동견적-${formData.customerName}-${formData.pages}페이지-${formData.quantity}부`;
    window.open(naverShoppingUrl, '_blank');
    
    // 모달 닫기
    const modal = bootstrap.Modal.getInstance(document.getElementById('naverPlaceModal'));
    modal.hide();
}

// 견적서 미리보기 함수
function previewQuote() {
    console.log('견적서 미리보기 시작');
    
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email') ? document.getElementById('email').value : '',
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };
    
    // 필수 필드 확인
    if (!formData.customerName || !formData.pages || !formData.printType || !formData.bindingType || !formData.quantity) {
        showAlert('모든 필드를 입력해주세요.', 'warning');
        return;
    }
    
    // 로딩 표시
    const previewBtn = document.getElementById('previewBtn');
    if (!previewBtn) {
        console.error('previewBtn 요소를 찾을 수 없습니다');
        showAlert('미리보기 버튼을 찾을 수 없습니다.', 'danger');
        return;
    }
    
    const originalText = previewBtn.innerHTML;
    previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>미리보기 생성 중...';
    previewBtn.disabled = true;
    
    console.log('미리보기 요청 시작');
    
    // 미리보기 요청
    fetch('/preview_quote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('미리보기 응답 상태:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('미리보기 응답 데이터:', data);
        if (data.success) {
            showTextPreview(data.price_info);
        } else {
            throw new Error(data.error || '미리보기 생성 실패');
        }
    })
    .catch(error => {
        console.error('미리보기 오류:', error);
        showAlert('미리보기 생성 중 오류가 발생했습니다: ' + error.message, 'danger');
    })
    .finally(() => {
        // 버튼 상태 복원
        previewBtn.innerHTML = originalText;
        previewBtn.disabled = false;
        console.log('미리보기 함수 완료');
    });
}

// 상품명 생성 함수
function getProductName(formData) {
    const printType = formData.printType || '흑백';
    const printMethod = formData.printMethod || 'single';
    const bindingType = formData.bindingType || '무선';
    
    // 한글 표기 맵핑
    const typeKo = {
        '흑백': '흑백',
        'black_white': '흑백',
        '잉크칼라': '잉크 칼라',
        'ink_color': '잉크 칼라',
        '레이져칼라': '레이저 칼라',
        'laser_color': '레이저 칼라'
    }[printType] || printType;
    
    const bindingKo = {
        '무선': '무선',
        'ring': '링',
        'perfect': '무선',
        'saddle': '중철'
    }[bindingType] || bindingType;
    
    let methodText = '단면';
    if (printMethod === 'double') {
        methodText = '양면';
    }
    
    return `${typeKo} ${methodText} ${bindingKo}제본`;
}

// 텍스트 미리보기 모달 표시 (온누리인쇄나라 견적서 양식)
// 견적서 미리보기 함수 (깔끔한 버전)
function showTextPreview(priceInfo) {
    console.log('미리보기 priceInfo 데이터:', priceInfo);
    
    const formData = {
        customerName: document.getElementById('customerName').value,
        email: document.getElementById('email') ? document.getElementById('email').value : '',
        pages: parseInt(document.getElementById('pages').value),
        printType: document.getElementById('printType').value,
        printMethod: document.getElementById('printMethod').value,
        bindingType: document.getElementById('bindingType').value,
        quantity: parseInt(document.getElementById('quantity').value)
    };

    // 새로운 깔끔한 모달 HTML
    const modalHtml = `
    <div class="modal fade" id="previewModal" tabindex="-1" aria-labelledby="previewModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="previewModalLabel">
                        <i class="fas fa-eye me-2"></i>견적서 미리보기
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" style="padding: 20px; background: #f8f9fa;">
                    <div class="page a4" style="width: 100%; max-width: 900px; margin: 0 auto; font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif; color: #000; padding: 0; display: block;">
                        <!-- 견적서 상자 -->
                        <div style="border: 1px solid #c3e6cb; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                            <!-- 상단: 견적서 제목 -->
                            <h1 style="color: #155724; font-size: 28px; font-weight: bold; text-align: center; margin-bottom: 30px;">
                                견적서
                            </h1>
                            
                            <!-- 상단 정보 영역 (세로 확대, 크기 동일, 폰트 더 작게) -->
                            <div style="display: flex; margin-bottom: 25px; gap: 20px; align-items: stretch; height: 180px; width: 100%;">
                                <!-- 좌측: 수신인 정보 (세로 확대) -->
                                <div style="flex: 1; text-align: left; padding: 15px; border: 1px solid #ddd; border-radius: 6px; display: flex; flex-direction: column; justify-content: space-between;">
                                    <div>
                                        <div style="margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #333;">수신인</div>
                                        <div style="margin-bottom: 12px; font-size: 12px;">
                                            <strong>수신 :</strong> ${formData.customerName || '12'} 귀하
                                        </div>
                                        <div style="margin-bottom: 15px; font-size: 12px;">
                                            <strong>견적일자 :</strong> ${new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}
                                        </div>
                                    </div>
                                    <div style="font-size: 11px; font-style: italic; color: #666; text-align: center;">
                                        아래와 같이 견적합니다.
                                    </div>
                                </div>
                                
                                <!-- 우측: 공급자 정보 (세로 확대, 크기 동일, 폰트 더 작게) -->
                                <div style="flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; display: flex; flex-direction: column; align-items: stretch; justify-content: center; overflow: hidden;">
                                    <!-- 상단 라벨 -->
                                    <div style="background: #e9ecef; padding: 6px; text-align: center; font-weight: bold; font-size: 12px; color: #333; border-radius: 5px 5px 0 0; margin-bottom: 0;">
                                        공급자
                                    </div>
                                    
                                    <!-- 하단 테이블 (세로 확대, 폰트 더 작게) -->
                                    <div style="flex: 1; background: #f8f9fa; border-radius: 0 0 5px 5px; padding: 8px; overflow: hidden;">
                                        <table style="width: 100%; height: 100%; border-collapse: collapse; font-size: 6px; table-layout: fixed;">
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold; width: 20%;">상호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">온누리인쇄나라</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold; width: 20%;">대표자</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;">류도현</td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">사업자번호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">491-20-00640</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;"></td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;"></td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">주소</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;" colspan="3">서울 금천구 가산디지털1로 142 가산더스카이밸리1차 3층 816호</td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">업태</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">제조, 소매, 서비스업</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">종목</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;">경인쇄, 문구, 출력, 복사, 제본</td>
                                            </tr>
                                            <tr>
                                                <td style="border: 1px solid #ccc; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">사업자계좌번호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #fff;">신한 110-493-223413</td>
                                                <td style="border: 1px solid #ccc; border-left: none; border-right: none; padding: 3px; background: #e9ecef; font-weight: bold;">전화번호</td>
                                                <td style="border: 1px solid #ccc; border-left: none; padding: 3px; background: #fff;">02-6338-7123</td>
                                            </tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 합계금액 (총비용 + 세액) -->
                            <div style="margin-bottom: 80px; margin-top: 40px; padding: 15px; background: #e3f2fd; border: 1px solid #2196f3; border-radius: 6px; text-align: center;">
                                <div style="font-size: 16px; font-weight: bold; color: #1976d2;">
                                    합계금액: 일금 ${(priceInfo.total_price + (priceInfo.tax_amount || Math.round(priceInfo.total_price * 0.1))).toLocaleString()}원정
                                </div>
                            </div>
                            
                            
                            <!-- 견적 내용 테이블 (간격 더 확대) -->
                            <div style="margin-bottom: 120px; margin-top: 30px;">
                                <div style="font-size: 12px; font-weight: bold; color: #333; margin-bottom: 8px;">견적 내용</div>
                                <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; border-radius: 5px; overflow: hidden;">
                                    <thead>
                                        <tr style="background: #f8f9fa;">
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 20%; text-align: center;">상품명</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 12%; text-align: center;">규격</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 12%; text-align: center;">수량</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 18%; text-align: center;">부당 단가(부가세 제외)</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 18%; text-align: center;">총비용(부가세 제외)</th>
                                            <th style="border: 1px solid #ddd; padding: 10px; font-size: 10px; font-weight: bold; width: 20%; text-align: center;">세액</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${getProductName(formData)}</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${formData.size || 'A4'}</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${parseInt(formData.quantity).toLocaleString()}권</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${priceInfo.unit_price.toLocaleString()}원</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${priceInfo.total_price.toLocaleString()}원</td>
                                            <td style="border: 1px solid #ddd; padding: 10px; font-size: 10px; text-align: center;">${priceInfo.tax_amount ? priceInfo.tax_amount.toLocaleString() : Math.round(priceInfo.total_price * 0.1).toLocaleString()}원</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            
                            <!-- 하단 서명 (간격 더 확대) -->
                            <div style="margin-top: 60px; padding: 25px; border: 1px solid #ddd; border-radius: 6px; text-align: right;">
                                <div style="margin-bottom: 10px; font-size: 14px; color: #333; font-weight: bold;">${new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })}</div>
                                <div style="margin-bottom: 10px; font-size: 14px; color: #333; font-weight: bold;">온누리인쇄나라</div>
                                <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px;">
                                    <span style="font-size: 14px; color: #333; font-weight: bold;">류도현</span>
                                    <img src="static/images/도장.png" alt="도장" style="width: 35px; height: 35px;" onerror="this.style.display='none';">
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        <i class="fas fa-times me-2"></i>닫기
                    </button>
                    <button type="button" class="btn btn-primary" onclick="printPreview()">
                        <i class="fas fa-print me-2"></i>인쇄 (PDF 저장)
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // 기존 모달 제거
    const existingModal = document.getElementById('previewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 새 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

// 간단한 인쇄 함수 (브라우저 기본 인쇄 기능 사용)
// PDF 다운로드 함수 (간단하고 확실한 방법)
function printPreview() {
    const modal = document.getElementById('previewModal');
    const modalBody = modal.querySelector('.modal-body');
    
    if (!modalBody) {
        showAlert('미리보기 데이터를 찾을 수 없습니다.', 'danger');
        return;
    }
    
    // 저장 안내 메시지
    const saveMessage = `
        📁 PDF 저장 안내
        
        인쇄 대화상자가 열리면:
        1. "대상"을 "PDF로 저장" 선택
        2. 파일명을 "견적서_${new Date().toISOString().slice(0,10)}.pdf"로 설정
        3. 저장 버튼 클릭
        
        💡 이 방법이 가장 확실합니다!
    `;
    
    // 안내 메시지 표시
    showAlert(saveMessage, 'info');
    
    // 2초 후 인쇄 창 열기
    setTimeout(() => {
        // 새 창 열기
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        
        // 인쇄용 HTML 생성
        const printContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>견적서</title>
                <style>
                    @page {
                        size: A4 portrait;
                        margin: 15mm;
                    }
                    body {
                        font-family: 'Malgun Gothic', 'Noto Sans CJK KR', Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        font-size: 12px;
                        line-height: 1.4;
                        background: white;
                        color: #000;
                    }
                    .page {
                        width: 100%;
                        max-width: 180mm;
                        margin: 0 auto;
                        background: white;
                        padding: 0;
                    }
                    @media print {
                        body {
                            -webkit-print-color-adjust: exact;
                            print-color-adjust: exact;
                        }
                        .page {
                            max-width: none;
                            width: 100%;
                        }
                        table {
                            page-break-inside: avoid;
                        }
                        .no-print {
                            display: none !important;
                        }
                    }
                    @media screen {
                        body {
                            padding: 20px;
                        }
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
            setTimeout(function() {
                printWindow.print();
                // 3초 후 창 닫기
                setTimeout(function() {
                    printWindow.close();
                }, 3000);
            }, 1000);
        };
    }, 2000);
}

// 숫자를 한글로 변환하는 함수
function convertNumberToKorean(number) {
    if (number == 0) return '영';
    
    const units = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구'];
    const tens = ['', '십', '백', '천'];
    const bigUnits = ['', '만', '억', '조'];
    
    const numStr = number.toString().split('').reverse().join('');
    const result = [];
    
    for (let i = 0; i < numStr.length; i++) {
        const digit = numStr[i];
        if (digit === '0') continue;
        
        if (i % 4 === 0 && i > 0) {
            const bigUnitIdx = Math.floor(i / 4);
            if (bigUnitIdx < bigUnits.length) {
                result.push(bigUnits[bigUnitIdx]);
            }
        }
        
        const smallUnitIdx = i % 4;
        if (smallUnitIdx > 0 && digit !== '1') {
            result.push(tens[smallUnitIdx]);
        } else if (smallUnitIdx > 0 && digit === '1') {
            result.push(tens[smallUnitIdx]);
        }
        
        if (digit !== '1' || smallUnitIdx === 0) {
            result.push(units[parseInt(digit)]);
        }
    }
    
    return result.reverse().join('');
}

// 스크롤 애니메이션 초기화
function initScrollAnimations() {
    const elements = document.querySelectorAll('.fade-in');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, {
        threshold: 0.1
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// 부드러운 스크롤 초기화
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// 알림 표시
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // 3초 후 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

// 전화번호 클릭 시 전화 걸기
function makeCall(phoneNumber) {
    window.location.href = `tel:${phoneNumber}`;
}

// 네이버블로그 열기
function openNaverBlog() {
    const blogUrl = 'https://blog.naver.com/onnuriinsenara';
    window.open(blogUrl, '_blank');
}

// 실시간 견적 미리보기
function updateQuotePreview() {
    const pages = parseInt(document.getElementById('pages').value) || 0;
    const printType = document.getElementById('printType').value;
    const quantity = parseInt(document.getElementById('quantity').value) || 0;
    
    if (pages > 0 && quantity > 0) {
        // 간단한 미리보기 계산
        const basePrices = {
            'black_white': 50,
            'ink_color': 200,
            'laser_color': 300
        };
        
        const unitPrice = basePrices[printType] * pages;
        const totalPrice = unitPrice * quantity;
        
        // 미리보기 표시 (선택사항)
        console.log(`예상 가격: ${totalPrice.toLocaleString()}원`);
    }
}

// 폼 유효성 검사
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// 숫자 입력 포맷팅
function formatNumber(input) {
    const value = input.value.replace(/[^0-9]/g, '');
    input.value = value;
}

// 포트폴리오 로딩
let currentCategory = 'all';
let portfolioPage = 0;

async function loadPortfolio(category = 'all', reset = false) {
    if (reset) {
        portfolioPage = 0;
        currentCategory = category;
    }
    
    const portfolioGrid = document.getElementById('portfolioGrid');
    if (!portfolioGrid) return;
    
    try {
        const response = await fetch(`/portfolio?category=${category}`);
        const data = await response.json();
        
        if (data.success && data.portfolios) {
            if (reset) {
                portfolioGrid.innerHTML = '';
            }
            
            if (data.portfolios.length === 0) {
                portfolioGrid.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fas fa-images fa-3x text-muted mb-3"></i>
                        <p class="text-muted">표시할 포트폴리오가 없습니다.</p>
                    </div>
                `;
                return;
            }
            
            data.portfolios.forEach(portfolio => {
                const col = document.createElement('div');
                col.className = 'col-md-4 col-lg-3 mb-4';
                const imagePath = portfolio.thumbnail_path ? '/static/' + portfolio.thumbnail_path : '/static/' + portfolio.image_path;
                const fullImagePath = '/static/' + portfolio.image_path;
                const safeTitle = portfolio.title.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                const safeCategory = portfolio.category.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                
                col.innerHTML = `
                    <div class="card portfolio-card h-100" style="cursor: pointer;">
                        <img src="${imagePath}" 
                             class="card-img-top portfolio-image" 
                             alt="${portfolio.title}" 
                             style="height: 200px; object-fit: cover; user-select: none !important; -webkit-user-select: none !important; -moz-user-select: none !important; -ms-user-select: none !important; pointer-events: auto;"
                             data-full-image="${fullImagePath}"
                             data-title="${safeTitle}"
                             data-category="${safeCategory}">
                        <div class="card-body">
                            <h6 class="card-title">${portfolio.title}</h6>
                            <p class="card-text">
                                <small class="text-muted">
                                    <i class="fas fa-tag me-1"></i>${portfolio.category}
                                </small>
                            </p>
                        </div>
                    </div>
                `;
                
                // 이미지에 이벤트 리스너 직접 추가
                const img = col.querySelector('.portfolio-image');
                if (img) {
                    // 복사 방지 이벤트
                    img.addEventListener('contextmenu', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    });
                    
                    img.addEventListener('selectstart', function(e) {
                        e.preventDefault();
                        return false;
                    });
                    
                    img.addEventListener('dragstart', function(e) {
                        e.preventDefault();
                        return false;
                    });
                    
                    // 클릭 이벤트
                    img.addEventListener('click', function() {
                        showPortfolioModal(fullImagePath, portfolio.title, portfolio.category);
                    });
                    
                    // 카드 전체 클릭 이벤트
                    const card = col.querySelector('.portfolio-card');
                    if (card) {
                        card.addEventListener('click', function(e) {
                            if (e.target !== img && !img.contains(e.target)) {
                                showPortfolioModal(fullImagePath, portfolio.title, portfolio.category);
                            }
                        });
                    }
                }
                
                portfolioGrid.appendChild(col);
            });
        }
    } catch (error) {
        console.error('포트폴리오 로딩 오류:', error);
        portfolioGrid.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <p class="text-danger">포트폴리오를 불러오는 중 오류가 발생했습니다.</p>
            </div>
        `;
    }
}

function filterPortfolio(category) {
    // 버튼 활성화 상태 업데이트
    const filterGroup = document.getElementById('portfolioCategoryFilter');
    if (filterGroup) {
        filterGroup.querySelectorAll('button').forEach(btn => {
            btn.classList.remove('active');
        });
        // 해당 카테고리 버튼 활성화
        filterGroup.querySelectorAll('button').forEach(btn => {
            if (btn.textContent.trim() === category || (category === 'all' && btn.textContent.trim() === '전체')) {
                btn.classList.add('active');
            }
        });
    }
    
    loadPortfolio(category, true);
}

// 포트폴리오 이미지 모달 표시
function showPortfolioModal(imagePath, title, category) {
    // 기존 모달이 있으면 제거
    const existingModal = document.getElementById('portfolioImageModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // 모달 HTML 생성
    const safeTitle = String(title).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    const safeCategory = String(category).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    
    const modalHtml = `
        <div class="modal fade" id="portfolioImageModal" tabindex="-1" aria-labelledby="portfolioImageModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="portfolioImageModalLabel">
                            <i class="fas fa-image me-2"></i>${safeTitle}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center p-0">
                        <img src="${imagePath}" 
                             class="img-fluid portfolio-modal-image" 
                             alt="${safeTitle}"
                             style="max-height: 70vh; width: auto; user-select: none !important; -webkit-user-select: none !important; -moz-user-select: none !important; -ms-user-select: none !important; pointer-events: auto;">
                        <div class="p-3">
                            <p class="mb-1"><strong>제목:</strong> ${safeTitle}</p>
                            <p class="mb-0 text-muted"><i class="fas fa-tag me-1"></i>${safeCategory}</p>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            <i class="fas fa-times me-2"></i>닫기
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 모달 추가
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 모달 이미지에 복사 방지 이벤트 추가
    setTimeout(() => {
        const modalImg = document.querySelector('#portfolioImageModal .portfolio-modal-image');
        if (modalImg) {
            modalImg.addEventListener('contextmenu', function(e) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            });
            
            modalImg.addEventListener('selectstart', function(e) {
                e.preventDefault();
                return false;
            });
            
            modalImg.addEventListener('dragstart', function(e) {
                e.preventDefault();
                return false;
            });
            
            modalImg.setAttribute('draggable', 'false');
        }
    }, 100);
    
    // Bootstrap 모달 표시
    const modal = new bootstrap.Modal(document.getElementById('portfolioImageModal'));
    modal.show();
    
    // 모달이 닫힐 때 제거
    document.getElementById('portfolioImageModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// 서비스별 포트폴리오 보기
function showServicePortfolio(serviceName, serviceDisplayName) {
    // 포트폴리오 섹션으로 스크롤
    const portfolioSection = document.getElementById('portfolio');
    if (portfolioSection) {
        portfolioSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // 서비스 이름을 포트폴리오 카테고리로 매핑 시도
        // 서비스 이름과 포트폴리오 카테고리 매핑
        const categoryMapping = {
            'coil_binding': '책자',
            'wire_binding': '책자',
            'perfect_binding': '책자',
            'saddle_binding': '책자',
            'leaflet': '전단지',
            'brochure': '브로슈어'
        };
        
        // 매핑된 카테고리가 있으면 해당 카테고리로 필터링, 없으면 전체 표시
        const mappedCategory = categoryMapping[serviceName] || 'all';
        
        // 약간의 지연 후 필터링 (스크롤 애니메이션 완료 대기)
        setTimeout(() => {
            filterPortfolio(mappedCategory);
        }, 500);
    } else {
        // 포트폴리오 섹션이 없으면 전체로 필터링
        loadPortfolio('all', true);
    }
}

// [해결] 갤러리 무한 추가 방지 자바스크립트
let isFetching = false;

function loadMorePortfolio() {
    if (isFetching) return;
    isFetching = true;
    
    const btn = document.getElementById('loadMoreBtn');
    if (!btn) {
        isFetching = false;
        return;
    }
    
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 로딩 중...';
    btn.disabled = true;

    portfolioPage++;
    
    fetch(`/api/portfolio?page=${portfolioPage}&category=${currentCategory}&per_page=12`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('portfolioGrid');
            if (!container) {
                isFetching = false;
                btn.innerHTML = originalText;
                btn.disabled = false;
                return;
            }
            
            // 데이터가 없거나 실패한 경우 버튼 숨김
            if (!data.success || !data.items || data.items.length === 0) {
                btn.style.display = 'none';
                isFetching = false;
                btn.innerHTML = originalText;
                btn.disabled = false;
                return;
            }
            
            // 실제로 추가된 항목 수 추적
            let addedCount = 0;
            
            data.items.forEach(item => {
                // ID 중복 체크: 이미 화면에 있는 사진은 추가하지 않음
                if (!document.querySelector(`.portfolio-item[data-id="${item.id}"]`)) {
                    const imagePath = item.thumbnail_path ? '/static/' + item.thumbnail_path : '/static/' + item.image_path;
                    const fullImagePath = '/static/' + item.image_path;
                    const safeTitle = item.title.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    const safeCategory = item.category.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                    
                    const col = document.createElement('div');
                    col.className = 'col-md-4 col-lg-3 mb-4 portfolio-item';
                    col.setAttribute('data-id', item.id);
                    
                    col.innerHTML = `
                        <div class="card portfolio-card h-100" style="cursor: pointer;">
                            <img src="${imagePath}" 
                                 class="card-img-top portfolio-image" 
                                 alt="${item.title}" 
                                 style="height: 200px; object-fit: cover; user-select: none !important; -webkit-user-select: none !important; -moz-user-select: none !important; -ms-user-select: none !important; pointer-events: auto;"
                                 data-full-image="${fullImagePath}"
                                 data-title="${safeTitle}"
                                 data-category="${safeCategory}">
                            <div class="card-body">
                                <h6 class="card-title">${item.title}</h6>
                                <p class="card-text">
                                    <small class="text-muted">
                                        <i class="fas fa-tag me-1"></i>${item.category}
                                    </small>
                                </p>
                            </div>
                        </div>
                    `;
                    
                    // 이미지에 이벤트 리스너 직접 추가
                    const img = col.querySelector('.portfolio-image');
                    if (img) {
                        // 복사 방지 이벤트
                        img.addEventListener('contextmenu', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            return false;
                        });
                        
                        img.addEventListener('selectstart', function(e) {
                            e.preventDefault();
                            return false;
                        });
                        
                        img.addEventListener('dragstart', function(e) {
                            e.preventDefault();
                            return false;
                        });
                        
                        // 클릭 이벤트
                        img.addEventListener('click', function() {
                            showPortfolioModal(fullImagePath, item.title, item.category);
                        });
                        
                        // 카드 전체 클릭 이벤트
                        const card = col.querySelector('.portfolio-card');
                        if (card) {
                            card.addEventListener('click', function(e) {
                                if (e.target !== img && !img.contains(e.target)) {
                                    showPortfolioModal(fullImagePath, item.title, item.category);
                                }
                            });
                        }
                    }
                    
                    container.appendChild(col);
                    addedCount++;
                }
            });
            
            // 실제로 추가된 항목이 없거나, 더 이상 데이터가 없으면 버튼 숨김
            if (addedCount === 0 || !data.has_next || data.items.length === 0) {
                btn.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('포트폴리오 로딩 오류:', error);
        })
        .finally(() => {
            isFetching = false;
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// 견적 계산 영역 보호 (관리자만 수정 가능)
let originalFormValues = {};
let isFormProtected = false;

function protectQuoteForm() {
    // 보호 기능 완전 비활성화: 일반 사용자도 자유롭게 입력/수정 가능
    isFormProtected = false;
    return;

    // 아래 코드는 비활성화 상태로 남겨둠 (필요 시 다시 사용할 수 있음)
    const isAdmin = true;
    if (!isAdmin) {
        isFormProtected = true;
        const quoteForm = document.getElementById('quoteForm');
        if (quoteForm) {
            // 원본 값 저장
            const inputs = quoteForm.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                const inputId = input.id || input.name;
                originalFormValues[inputId] = input.value;
                input.setAttribute('data-protected', 'true');
                input.setAttribute('data-original-value', input.value);
                
                // 값 변경 감지 및 복원 (즉시)
                input.addEventListener('input', function(e) {
                    if (isFormProtected && this.getAttribute('data-protected') === 'true') {
                        const originalValue = this.getAttribute('data-original-value');
                        if (this.value !== originalValue) {
                            // 즉시 복원
                            // 보호 기능 비활성화: 값 복원/알림 수행 안 함
                            // this.value = originalValue;
                            // this.setAttribute('value', originalValue);
                            // e.preventDefault();
                            // e.stopPropagation();
                            // alert('견적 계산 영역은 보호되어 있습니다. 수정/삭제는 관리자만 가능합니다.');
                            // return false;
                        }
                    }
                });
                
                // 값 변경 감지 (select의 경우)
                input.addEventListener('change', function(e) {
                    if (isFormProtected && this.getAttribute('data-protected') === 'true') {
                        const originalValue = this.getAttribute('data-original-value');
                        if (this.value !== originalValue) {
                            // 즉시 복원
                            // 보호 기능 비활성화: 값 복원/알림 수행 안 함
                            // this.value = originalValue;
                            // this.setAttribute('value', originalValue);
                            // const options = this.querySelectorAll('option');
                            // options.forEach(option => {
                            //     if (option.value === originalValue) {
                            //         option.selected = true;
                            //     } else {
                            //         option.selected = false;
                            //     }
                            // });
                            // e.preventDefault();
                            // e.stopPropagation();
                            // alert('견적 계산 영역은 보호되어 있습니다. 수정/삭제는 관리자만 가능합니다.');
                            // return false;
                        }
                    }
                });
                
                // 키 입력 방지 (일부 키)
                input.addEventListener('keydown', function(e) {
                    if (isFormProtected && this.getAttribute('data-protected') === 'true') {
                        // Delete, Backspace 등 방지
                        if (e.key === 'Delete' || e.key === 'Backspace') {
                            const originalValue = this.getAttribute('data-original-value');
                            if (this.value === originalValue) {
                                e.preventDefault();
                                e.stopPropagation();
                                return false;
                            }
                        }
                    }
                });
                
                // 더블클릭 방지 기능 비활성화
                // input.addEventListener('dblclick', function(e) {
                //     e.preventDefault();
                //     e.stopPropagation();
                //     alert('견적 계산 영역은 보호되어 있습니다. 수정/삭제는 관리자만 가능합니다.');
                //     return false;
                // });
                
                // 우클릭 메뉴 방지
                input.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                });
                
                // 키보드 단축키 방지
                input.addEventListener('keydown', function(e) {
                    // 개발자도구 방지 기능 비활성화
                    // if (e.key === 'F12' || 
                    //     (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) ||
                    //     (e.ctrlKey && e.key === 'U')) {
                    //     e.preventDefault();
                    //     e.stopPropagation();
                    //     alert('견적 계산 영역은 보호되어 있습니다.');
                    //     return false;
                    // }
                });
            });
            
            // 폼 자체 수정 방지
            quoteForm.addEventListener('submit', function(e) {
                // 일반 제출은 허용 (견적 계산)
                return true;
            });
            
            // DOM 변경 감지 (MutationObserver) - 강화
            const observer = new MutationObserver(function(mutations) {
                if (isFormProtected) {
                    mutations.forEach(function(mutation) {
                        const target = mutation.target;
                        if (target.getAttribute && target.getAttribute('data-protected') === 'true') {
                            const originalValue = target.getAttribute('data-original-value');
                            if (target.value && target.value !== originalValue) {
                                target.value = originalValue;
                                target.setAttribute('value', originalValue);
                            }
                        }
                        
                        // 속성 변경 감지
                        if (mutation.type === 'attributes') {
                            const attrName = mutation.attributeName;
                            if (attrName === 'value' || attrName === 'selected') {
                                const originalValue = target.getAttribute('data-original-value');
                                if (target.value !== originalValue) {
                                    target.value = originalValue;
                                }
                            }
                        }
                    });
                }
            });
            
            // 폼 전체 감시 (더 강력하게)
            observer.observe(quoteForm, {
                attributes: true,
                attributeFilter: ['value', 'selected', 'checked', 'disabled', 'readonly'],
                childList: true,
                subtree: true,
                characterData: true
            });
            
            // 주기적으로 값 검증 및 복원 (계산 중이 아닐 때만)
            setInterval(function() {
                if (isFormProtected && !window.isCalculating) {
                    const currentInputs = quoteForm.querySelectorAll('input, select, textarea');
                    currentInputs.forEach(input => {
                        if (input.getAttribute('data-protected') === 'true') {
                            const originalValue = input.getAttribute('data-original-value');
                            // 계산 중이 아니고 값이 변경된 경우에만 복원
                            if (input.value !== originalValue) {
                                input.value = originalValue;
                                input.setAttribute('value', originalValue);
                                // select의 경우
                                if (input.tagName === 'SELECT') {
                                    const options = input.querySelectorAll('option');
                                    options.forEach(option => {
                                        if (option.value === originalValue) {
                                            option.selected = true;
                                        } else {
                                            option.selected = false;
                                        }
                                    });
                                }
                            }
                        }
                    });
                }
            }, 100); // 100ms마다 검증 (더 빠르게)
            
            // JavaScript를 통한 직접 수정 방지 (강화)
            try {
                // 폼 innerHTML 수정 방지
                const formInnerHTMLDescriptor = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
                if (formInnerHTMLDescriptor) {
                    Object.defineProperty(quoteForm, 'innerHTML', {
                        set: function(value) {
                            if (isFormProtected) {
                                console.warn('견적 계산 영역은 보호되어 있습니다.');
                                return;
                            }
                            formInnerHTMLDescriptor.set.call(this, value);
                        },
                        get: function() {
                            return formInnerHTMLDescriptor.get.call(this);
                        },
                        configurable: false,
                        enumerable: true
                    });
                }
            } catch (e) {
                console.warn('폼 보호 설정 중 오류:', e);
            }
            
            // 폼 필드 직접 접근 방지 (강화)
            inputs.forEach(input => {
                try {
                    // value 속성 보호
                    let originalValue = input.getAttribute('data-original-value') || input.value;
                    
                    Object.defineProperty(input, 'value', {
                        set: function(newValue) {
                            if (isFormProtected && this.getAttribute('data-protected') === 'true') {
                                const protectedValue = this.getAttribute('data-original-value');
                                // 계산 버튼 클릭 시에만 값 변경 허용
                                if (newValue !== protectedValue && !window.isCalculating) {
                                    console.warn('견적 계산 영역은 보호되어 있습니다.');
                                    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(this, protectedValue);
                                    return;
                                }
                            }
                            Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(this, newValue);
                        },
                        get: function() {
                            return Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').get.call(this);
                        },
                        configurable: false,
                        enumerable: true
                    });
                    
                    // setAttribute 보호
                    const originalSetAttribute = input.setAttribute.bind(input);
                    input.setAttribute = function(name, value) {
                        if (isFormProtected && this.getAttribute('data-protected') === 'true') {
                            if (name === 'value' || name === 'data-original-value') {
                                // 원본 값 변경 방지
                                return;
                            }
                        }
                        originalSetAttribute(name, value);
                    };
                } catch (e) {
                    console.warn('입력 필드 보호 설정 중 오류:', e);
                }
            });
            
            // 견적 결과 영역 보호
            const quoteResult = document.getElementById('quoteResult');
            if (quoteResult) {
                quoteResult.setAttribute('data-protected', 'true');
                
                // 결과 영역 DOM 조작 방지
                const resultObserver = new MutationObserver(function(mutations) {
                    if (isFormProtected) {
                        mutations.forEach(function(mutation) {
                            if (mutation.type === 'childList' || mutation.type === 'attributes') {
                                console.warn('견적 결과 영역은 보호되어 있습니다.');
                            }
                        });
                    }
                });
                
                resultObserver.observe(quoteResult, {
                    childList: true,
                    attributes: true,
                    subtree: true
                });
            }
        }
    }
}

// 페이지 로드 완료 후 실행
window.addEventListener('load', function() {
    // 초기화 작업
    console.log('온누리인쇄나라 웹사이트가 로드되었습니다.');
    
    // 애니메이션 시작
    document.body.classList.add('loaded');
    
    // 견적 계산 영역 보호 기능은 비활성화 (일반 사용자는 자유롭게 입력 가능)
    //protectQuoteForm();
    
    // 포트폴리오 로딩
    if (document.getElementById('portfolioGrid')) {
        loadPortfolio('all', true);
    }
});