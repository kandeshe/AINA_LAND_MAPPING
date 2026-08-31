import csv
import numpy as np


def generate_groundwater_statistics(groundwater, output_folder):

    print("\nCalculating Groundwater Statistics...\n")

    if not groundwater:

        print("No groundwater data found.")

        return

    data = groundwater["data"]

    valid = data[np.isfinite(data)]

    minimum = float(np.min(valid))
    maximum = float(np.max(valid))
    mean = float(np.mean(valid))
    median = float(np.median(valid))
    std = float(np.std(valid))

    recharge = groundwater["recharge"]
    elevation = groundwater["elevation"]

    csv_file = output_folder / "GroundwaterStatistics.csv"

    with open(csv_file, "w", newline="") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "Parameter",
            "Value"
        ])

        writer.writerow(["Minimum Depth (m)", round(minimum, 2)])
        writer.writerow(["Maximum Depth (m)", round(maximum, 2)])
        writer.writerow(["Average Depth (m)", round(mean, 2)])
        writer.writerow(["Median Depth (m)", round(median, 2)])
        writer.writerow(["Standard Deviation", round(std, 2)])
        writer.writerow(["Recharge Potential (%)", round(recharge, 2)])
        writer.writerow(["Elevation (m)", round(elevation, 2)])

    report_file = output_folder / "Groundwater_Report.txt"

    with open(report_file, "w") as report:

        report.write("GROUNDWATER ANALYSIS REPORT\n")
        report.write("====================================\n\n")

        report.write(f"Elevation               : {elevation:.2f} m\n")
        report.write(f"Minimum Depth           : {minimum:.2f} m\n")
        report.write(f"Maximum Depth           : {maximum:.2f} m\n")
        report.write(f"Average Depth           : {mean:.2f} m\n")
        report.write(f"Median Depth            : {median:.2f} m\n")
        report.write(f"Standard Deviation      : {std:.2f}\n")
        report.write(f"Recharge Potential      : {recharge:.2f}%\n\n")

        report.write("GROUNDWATER INTERPRETATION\n")
        report.write("------------------------------------\n")

        if mean <= 10:
            report.write(
                "Groundwater is shallow and easily accessible.\n"
            )
            report.write(
                "Excellent for shallow borewells.\n"
            )

        elif mean <= 25:
            report.write(
                "Moderate groundwater depth.\n"
            )
            report.write(
                "Suitable for agricultural borewells.\n"
            )

        elif mean <= 50:
            report.write(
                "Groundwater occurs at deeper levels.\n"
            )
            report.write(
                "Deep borewell recommended.\n"
            )

        else:
            report.write(
                "Groundwater is very deep.\n"
            )
            report.write(
                "Hydrogeological investigation recommended before drilling.\n"
            )

        report.write("\nRecharge Assessment\n")
        report.write("------------------------------------\n")

        if recharge >= 80:
            report.write(
                "Excellent groundwater recharge potential.\n"
            )

        elif recharge >= 60:
            report.write(
                "Good recharge potential.\n"
            )

        elif recharge >= 40:
            report.write(
                "Moderate recharge potential.\n"
            )

        else:
            report.write(
                "Poor recharge potential.\n"
            )

        report.write("\nLARA Groundwater Module\n")

    print("CSV Saved")
    print("Report Saved")

    print("\n========== GROUNDWATER SUMMARY ==========")

    print(f"Elevation          : {elevation:.2f} m")
    print(f"Minimum Depth      : {minimum:.2f} m")
    print(f"Maximum Depth      : {maximum:.2f} m")
    print(f"Average Depth      : {mean:.2f} m")
    print(f"Recharge Potential : {recharge:.2f}%")

    print("\nGroundwater Statistics Completed Successfully.")
