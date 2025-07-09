import uuid
from flask import Flask, flash, make_response, redirect, render_template, request, url_for
import os
from models.order import Order, OrderItem
from models.product import Product
from models.base import db
from flask_migrate import Migrate, upgrade
import random
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates')

app.secret_key = 'supersecretkey'  # Para manter a sessão

metrics = GunicornPrometheusMetrics(app)
metrics.register_endpoint('/metrics')

teste = ""

# Configuração do banco de dados
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'ecommerce')
db_password = os.getenv('DB_PASSWORD', 'Pg1234')
db_name = os.getenv('DB_NAME', 'ecommerce')
db_port = os.getenv('DB_PORT', 5432)

db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# Inicializar SQLAlchemy e Flask-Migrate
db.init_app(app)
migrate = Migrate(app, db)

def generate_order_number():
    """Gera um número de pedido único com 6 dígitos."""
    return f'{random.randint(100000, 999999)}'

def apply_migrations():
    """Aplicar migrations automaticamente."""
    with app.app_context():
        try:
            upgrade()  # Aplicar todas as migrations pendentes
            print("Migrations applied successfully.")
        except Exception as e:
            print(f"Error applying migrations: {e}")

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/checkout', methods=['GET'])
def checkout_get():
    # Obtém o pedido pelo cookie
    order = get_order_from_cookie()

    if not order or not order.items:
        flash("Seu carrinho está vazio. Adicione produtos antes de prosseguir para o checkout.", "warning")
        return redirect(url_for('shop'))

    items = order.items  # Carrega os itens do pedido
    subtotal = sum(item.quantity * item.product.price for item in items)
    total = subtotal + 10  # Valor fixo de envio, por exemplo

    return render_template('checkout.html', items=items, subtotal=subtotal, total=total)


@app.route('/checkout', methods=['POST'])
def checkout():
    # Obtém dados do formulário de checkout
    user_name = f"{request.form['first_name']} {request.form['last_name']}"
    user_email = request.form['email']
    mobile = request.form['mobile']
    address1 = request.form['address1']
    address2 = request.form.get('address2', '')  # Opcional
    city = request.form['city']
    state = request.form['state']
    country = request.form.get('country', 'Brasil')  # Padrão para Brasil
    zip_code = request.form['zip']

    # Informações de pagamento
    card_name = request.form['card_name']
    card_number = request.form['card_number']
    expiry_date = request.form['expiry_date']
    cvv = request.form['cvv']

    # Verifica se há um pedido aberto
    order = Order.query.filter_by(is_open=True).first()
    if not order:
        flash("Não há itens no carrinho para finalizar o pedido.", "error")
        return redirect(url_for('cart'))

    # Atualiza o pedido com dados do usuário e do endereço
    order.user_name = user_name
    order.user_email = user_email
    order.mobile = mobile
    order.address1 = address1
    order.address2 = address2
    order.city = city
    order.state = state
    order.country = country
    order.zip_code = zip_code

    # Atualiza o pedido com informações do cartão de crédito
    order.card_name = card_name
    order.card_number = card_number
    order.expiry_date = expiry_date
    order.cvv = cvv

    # Gera um número único para o pedido e fecha o pedido
    order.order_number = generate_order_number()
    order.is_open = False

    # Salva as alterações no banco de dados
    db.session.commit()

    # Confirmação de sucesso
    flash(f"Pedido realizado com sucesso! Número do pedido: {order.order_number}", "success")
    return redirect(url_for('order_confirmation', order_number=order.order_number))


@app.route('/order_confirmation/<order_number>')
def order_confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number).first()
    return render_template('order_confirmation.html', order=order)

@app.route('/shop')
def shop():
    products = Product.query.all()
    return render_template('shop.html', products=products)

def get_or_create_order():
    uuid_order_id = request.cookies.get('order_id')

    order = None
    response = None

    if uuid_order_id:
        order = Order.query.filter(
            Order.uuid == uuid_order_id, Order.is_open == True
        ).first()

    if not order:
        order = Order(uuid=uuid.uuid4(), total_price=0.0, is_open=True)
        db.session.add(order)
        db.session.commit()

        response = redirect(request.url)
        response.set_cookie('order_id', str(order.uuid))  # Convertendo UUID para string

    return order, response

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    print("Entrou no add_to_cart")
    order, response = get_or_create_order()
    quantity = int(request.form.get("quantity"))

    order_item = OrderItem.query.filter_by(order_id=order.id, product_id=product_id).first()

    if order_item:
        order_item.quantity += quantity
    else:
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=product.price
        )
        db.session.add(order_item)

    db.session.commit()

    flash(f'{product.name} adicionado ao carrinho!', 'success')

    redirect_response = make_response(redirect(url_for('detail', product_id=product.id)))

    if response:
        for cookie_key, cookie_value in response.headers.items():
            if cookie_key.startswith("Set-Cookie"):
                redirect_response.headers.add(cookie_key, cookie_value)

    return redirect_response

@app.route('/detail/<int:product_id>')
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.limit(4).all()
    return render_template('detail.html', product=product, related_products=related_products)

def get_order_from_cookie():
    order_id = request.cookies.get('order_id')
    if not order_id:
        return None

    try:
        # Converte o valor do cookie para UUID
        uuid_order_id = uuid.UUID(order_id)
    except ValueError:
        # Retorna None se a conversão falhar
        return None

    # Ajuste na consulta para converter explicitamente para string
    return Order.query.filter(
        Order.uuid == str(uuid_order_id), Order.is_open == True
    ).first()


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    order = get_order_from_cookie()
    if not order:
        flash('Seu carrinho está vazio.', 'warning')
        return render_template('cart.html', items=[], subtotal=0, total=0)

    items = order.items
    subtotal = sum(item.quantity * item.price for item in items)
    shipping = 10.0
    total = subtotal + shipping

    return render_template('cart.html', items=items, subtotal=subtotal, total=total)


@app.route('/update_quantity/<int:item_id>', methods=['POST'])
def update_quantity(item_id):
    new_quantity = int(request.form.get('quantity'))
    item = OrderItem.query.get_or_404(item_id)

    if new_quantity <= 0:
        db.session.delete(item)
    else:
        item.quantity = new_quantity

    db.session.commit()
    flash('Quantidade atualizada com sucesso!', 'success')
    return redirect(url_for('cart'))


@app.route('/remove_item/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    item = OrderItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    flash('Item removido do carrinho.', 'success')
    return redirect(url_for('cart'))


@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

if __name__ == '__main__':
    #apply_migrations()
    app.run(host='0.0.0.0', port=5000, debug=True)
