import csv


def generate_rainfall_statistics(rainfall_data, output_folder):

    print("\nCalculating Rainfall Statistics...\n")

    values = list(rainfall_data.values())

    total_rainfall = sum(values)

    average_rainfall = (
        total_rainfall / len(values)
        if values else 0
    )

    maximum_rainfall = max(values) if values else 0

    minimum_rainfall = min(values) if values else 0

    wettest_month = max(
        rainfall_data,
        key=rainfall_data.get
    )

    driest_month = min(
        rainfall_data,
        key=rainfall_data.get
    )

    csv_file = output_folder / "RainfallStatistics.csv"

    with open(
        csv_file,
        "w",
        newline=""
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "Month",
            "Rainfall (mm)"
        ])

        for month, rainfall in rainfall_data.items():

            writer.writerow([
                month,
                round(rainfall, 2)
            ])

    report_file = output_folder / "Rainfall_Report.txt"

    with open(report_file, "w") as report:

        report.write("RAINFALL ANALYSIS REPORT\n")
        report.write("==============================\n\n")

        report.write(
            f"Annual Rainfall : {total_rainfall:.2f} mm\n"
        )

        report.write(
            f"Average Monthly Rainfall : {average_rainfall:.2f} mm\n"
        )

        report.write(
            f"Maximum Monthly Rainfall : {maximum_rainfall:.2f} mm\n"
        )

        report.write(
            f"Minimum Monthly Rainfall : {minimum_rainfall:.2f} mm\n"
        )

        report.write(
            f"Wettest Month : {wettest_month}\n"
        )

        report.write(
            f"Driest Month : {driest_month}\n\n"
        )

        report.write("Monthly Rainfall\n")
        report.write("------------------------------\n")

        for month, rainfall in rainfall_data.items():

            report.write(
                f"{month:<12} : {rainfall:.2f} mm\n"
            )

    print("\n========== RAINFALL SUMMARY ==========")

    print(
        f"Annual Rainfall : {total_rainfall:.2f} mm"
    )

    print(
        f"Average Monthly : {average_rainfall:.2f} mm"
    )

    print(
        f"Wettest Month   : {wettest_month}"
    )

    print(
        f"Driest Month    : {driest_month}"
    )

    print(
        f"Maximum Monthly : {maximum_rainfall:.2f} mm"
    )

    print(
        f"Minimum Monthly : {minimum_rainfall:.2f} mm"
    )

    print("\nRainfall Statistics Completed Successfully.")
