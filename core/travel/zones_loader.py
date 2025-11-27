@commands.command(name="zones_sync")
@commands.has_permissions(administrator=True)
async def zones_sync(self, ctx):
    """
    Syncs zones from Google Sheets → zones.json → reloads registry.
    """

    import os
    from dotenv import load_dotenv
    load_dotenv()

    SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
    SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT")

    if not SHEET_ID or not SERVICE_ACCOUNT:
        return await ctx.send("❌ Missing GOOGLE_SHEET_ID or GOOGLE_SERVICE_ACCOUNT in .env")

    await ctx.send("🔄 Syncing zones from Google Sheets…")

    try:
        zones = load_sheet_zones(
            sheet_id=SHEET_ID,
            credentials_path=SERVICE_ACCOUNT
        )

        save_zones_file(zones)
        self.bot.zone_registry.load()

        await ctx.send("✅ **Zones synced & reloaded successfully!**")

    except Exception as e:
        await ctx.send(f"❌ **Zone sync failed:** `{e}`")