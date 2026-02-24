import pytest


@pytest.fixture
def kontakt_html():
    return """
    <div class="product-item">
        <a href="/iphone-15-128gb.html" class="product-item-link">Apple iPhone 15 128GB Black</a>
        <span class="price" data-price-amount="1799.00">1 799 ₼</span>
        <img src="/media/catalog/product/iphone15.jpg" />
    </div>
    <div class="product-item">
        <a href="/iphone-15-256gb.html" class="product-item-link">Apple iPhone 15 256GB Blue</a>
        <span class="price" data-price-amount="2099.00">2 099 ₼</span>
        <img src="/media/catalog/product/iphone15-256.jpg" />
    </div>
    """


@pytest.fixture
def baku_electronics_html():
    return """
    <div class="product-card">
        <h3><a href="/products/iphone-15-128gb" class="product-card__name">iPhone 15 128GB</a></h3>
        <div class="product-card__price">1 749 ₼</div>
        <img src="/images/iphone15.webp" />
    </div>
    <div class="product-card">
        <h3><a href="/products/iphone-15-pro" class="product-card__name">iPhone 15 Pro 256GB</a></h3>
        <div class="product-card__price">2 899,00 ₼</div>
        <img src="/images/iphone15pro.webp" />
    </div>
    """


@pytest.fixture
def irshad_html():
    return """
    <div class="product-card">
        <a href="/product/apple-iphone-15" class="product-card__name">Apple iPhone 15 128GB</a>
        <span class="product-card__price">1.799,00 ₼</span>
        <img data-src="/uploads/iphone15.jpg" />
    </div>
    """


@pytest.fixture
def tap_az_html():
    return """
    <div class="products-i">
        <a href="/elan/12345" class="products-name">iPhone 15 128GB, yeni</a>
        <span class="products-price">1 650 AZN</span>
        <img src="/uploads/img1.jpg" />
    </div>
    <div class="products-i">
        <a href="/elan/12346" class="products-name">iPhone 15 Pro Max</a>
        <span class="products-price">2 800 AZN</span>
        <img src="/uploads/img2.jpg" />
        <span class="products-i__shop">Mağaza</span>
    </div>
    """


@pytest.fixture
def umico_html():
    return """
    <div class="product-card">
        <a href="/products/iphone-15-128" class="product-card__name">Apple iPhone 15 128GB</a>
        <div class="product-card__price">1 750 ₼</div>
        <img src="/images/products/iphone15.jpg" />
    </div>
    """


