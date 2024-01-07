from flask import Flask, render_template, request
import reporting_gen as rpg

app = Flask(__name__)

# Initialize the report generator pbject based on logic defined in reporting_gen.py
processor = rpg.Q1Processor('./files')
report_generator = rpg.Q1ReportGenerator(processor)

@app.route('/report')
def report():
    order = request.args.get('order', 'asc')
    report_data = report_generator.get_report_data(order)
    return render_template('report.html', drivers=report_data, order=order)


@app.route('/report/drivers/')
def drivers():
    order = request.args.get('order', 'asc')
    report_data = report_generator.get_all_drivers()
    return render_template('drivers.html', drivers=report_data, order=order)

@app.route('/report/drivers/<driver_id>')
def driver_info(driver_id):
    info = report_generator.get_driver_info(driver_id)
    return render_template('driver_info.html', driver_info=info, driver_id=driver_id)

if __name__ == '__main__':
    app.run(debug=True)


