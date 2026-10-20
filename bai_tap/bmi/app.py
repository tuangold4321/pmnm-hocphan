from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    height_raw = ''
    weight_raw = ''
    errors = {}
    result = None

    if request.method == 'POST':
        height_raw = request.form.get('height', '').strip()
        weight_raw = request.form.get('weight', '').strip()

        height_val = None
        weight_val = None
        if not height_raw:
            errors['height'] = 'Vui lòng nhập chiều cao.'
        else:
            try:
                h_str = height_raw.replace(',', '.')
                height_val = float(h_str)
                
                if height_val < 50 or height_val > 250:
                    errors['height'] = 'Giá trị phải từ 50 đến 250. (nhập mét thay vì cm)'
            except ValueError:
                errors['height'] = 'Vui lòng nhập một số.'

        if not weight_raw:
            errors['weight'] = 'Vui lòng nhập cân nặng.'
        else:
            try:
                w_str = weight_raw.replace(',', '.')
                weight_val = float(w_str)
                
                if weight_val < 10 or weight_val > 300:
                    errors['weight'] = 'Giá trị phải từ 10 đến 300.'
            except ValueError:
                errors['weight'] = 'Vui lòng nhập một số.'

        if not errors and height_val is not None and weight_val is not None:
            height_m = height_val / 100.0
            
            bmi = round(weight_val / (height_m ** 2), 1)

            if bmi < 18.5:
                category = 'Thiếu cân'
                color_name = 'vàng'
                css_class = 'yellow'
            elif bmi < 23.0:
                category = 'Bình thường'
                color_name = 'xanh'
                css_class = 'green'
            elif bmi < 25.0:
                category = 'Thừa cân'
                color_name = 'vàng'
                css_class = 'yellow'
            else:
                category = 'Béo phì'
                color_name = 'đỏ'
                css_class = 'red'

            weight_min = round(18.5 * (height_m ** 2), 1)
            weight_max = round(22.9 * (height_m ** 2), 1)

            result = {
                'bmi': bmi,
                'category': category,
                'color_name': color_name,
                'css_class': css_class,
                'weight_min': weight_min,
                'weight_max': weight_max
            }

    return render_template('index.html', 
                           height_raw=height_raw, 
                           weight_raw=weight_raw, 
                           errors=errors, 
                           result=result)

if __name__ == '__main__':
    app.run(debug=True)