import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";

/**
 * POST /api/generate-pdf?model=ECC100
 *
 * Generates a PDF from the preview page using headless Chromium,
 * uploads to Supabase Storage, bumps version, returns download URL.
 */
export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const model = searchParams.get("model");

  if (!model) {
    return NextResponse.json(
      { error: "Missing ?model= parameter" },
      { status: 400 }
    );
  }

  const supabase = createAdminClient();

  // Get the product
  const { data: product, error: productError } = await supabase
    .from("products")
    .select("id, model_name, current_version, product_line_id")
    .eq("model_name", model)
    .single();

  if (productError || !product) {
    return NextResponse.json(
      { error: `Product "${model}" not found` },
      { status: 404 }
    );
  }

  try {
    // Dynamically import to avoid bundling issues
    const chromium = (await import("@sparticuz/chromium")).default;
    const puppeteer = (await import("puppeteer-core")).default;

    // On Vercel, use the bundled chromium; locally, try to find Chrome
    const executablePath = process.env.VERCEL
      ? await chromium.executablePath()
      : process.platform === "darwin"
        ? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        : "/usr/bin/google-chrome";

    const browser = await puppeteer.launch({
      args: chromium.args,
      defaultViewport: { width: 612, height: 792 },
      executablePath,
      headless: true,
    });

    const page = await browser.newPage();

    // Build the preview URL
    const baseUrl =
      process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : `http://localhost:${process.env.PORT || 3000}`;

    await page.goto(`${baseUrl}/preview/${model}`, {
      waitUntil: "networkidle0",
      timeout: 30000,
    });

    // Generate PDF with US Letter size
    const pdfBuffer = await page.pdf({
      format: "Letter",
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });

    await browser.close();

    // Bump version
    const currentVer = product.current_version || "1.0";
    const parts = currentVer.split(".");
    const major = parseInt(parts[0]) || 1;
    const minor = (parseInt(parts[1]) || 0) + 1;
    const newVersion = `${major}.${minor}`;

    // Upload to Supabase Storage
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    const fileName = `DS_${model}_v${newVersion}_${today}.pdf`;
    const storagePath = `${model}/${fileName}`;

    const { error: uploadError } = await supabase.storage
      .from("datasheets")
      .upload(storagePath, pdfBuffer, {
        contentType: "application/pdf",
        upsert: true,
      });

    if (uploadError) {
      return NextResponse.json(
        { error: "PDF upload failed", details: uploadError.message },
        { status: 500 }
      );
    }

    // Get public URL
    const { data: urlData } = supabase.storage
      .from("datasheets")
      .getPublicUrl(storagePath);

    const pdfUrl = urlData.publicUrl;

    // Create version record
    await supabase.from("versions").insert({
      product_id: product.id,
      version: newVersion,
      changes: "PDF generated",
      pdf_storage_path: pdfUrl,
    });

    // Update product's current version
    await supabase
      .from("products")
      .update({ current_version: newVersion })
      .eq("id", product.id);

    // Log the change
    await supabase.from("change_logs").insert({
      product_id: product.id,
      product_line_id: product.product_line_id,
      changes_summary: `Generated PDF v${newVersion}`,
    });

    return NextResponse.json({
      ok: true,
      model,
      version: newVersion,
      fileName,
      pdfUrl,
    });
  } catch (err) {
    console.error("PDF generation error:", err);
    return NextResponse.json(
      {
        error: "PDF generation failed",
        details: err instanceof Error ? err.message : String(err),
      },
      { status: 500 }
    );
  }
}
