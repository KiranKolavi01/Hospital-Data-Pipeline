#!/bin/bash
# Backend Verification Script

echo "=========================================="
echo "Hospital Data Pipeline - Backend Verification"
echo "=========================================="
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "   ✅ Backend is running"
else
    echo "   ❌ Backend is not running. Start with: python main.py"
    exit 1
fi

# Check files exist
echo ""
echo "2. Checking output files..."
files=(
    "bronze/ehr.csv"
    "bronze/vitals.csv"
    "bronze/labs.csv"
    "silver/clean_vitals.csv"
    "silver/clean_labs.csv"
    "silver/patient_master.csv"
    "gold/anomalies.csv"
    "visualizations/hr_trend.png"
    "visualizations/oxygen_distribution.png"
    "visualizations/anomaly_counts.png"
    "hospital_pipeline.db"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
    fi
done

# Check API endpoints
echo ""
echo "3. Checking API endpoints..."
endpoints=(
    "/"
    "/vitals"
    "/labs"
    "/patient-master"
    "/anomalies"
    "/visualizations/hr_trend.png"
)

for endpoint in "${endpoints[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$endpoint")
    if [ "$status" = "200" ]; then
        echo "   ✅ GET $endpoint (HTTP $status)"
    else
        echo "   ❌ GET $endpoint (HTTP $status)"
    fi
done

# Check path traversal protection
echo ""
echo "4. Checking path traversal protection..."
status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/visualizations/../../etc/passwd")
if [ "$status" = "404" ] || [ "$status" = "400" ]; then
    echo "   ✅ Path traversal blocked (HTTP $status)"
else
    echo "   ❌ Path traversal NOT blocked (HTTP $status)"
fi

# Check database
echo ""
echo "5. Checking database..."
if [ -f "hospital_pipeline.db" ]; then
    tables=$(sqlite3 hospital_pipeline.db ".tables" 2>/dev/null)
    if echo "$tables" | grep -q "vitals"; then
        echo "   ✅ Database has all 4 tables"
        echo "   Row counts:"
        sqlite3 hospital_pipeline.db "SELECT '   - vitals: ' || COUNT(*) FROM vitals; SELECT '   - labs: ' || COUNT(*) FROM labs; SELECT '   - patient_master: ' || COUNT(*) FROM patient_master; SELECT '   - anomalies: ' || COUNT(*) FROM anomalies;"
    else
        echo "   ❌ Database tables missing"
    fi
else
    echo "   ❌ Database file not found"
fi

echo ""
echo "=========================================="
echo "Verification complete!"
echo "=========================================="
