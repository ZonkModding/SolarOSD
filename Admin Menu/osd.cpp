#include "osd.h"
#include <string>
#include <cmath>
#include <ctime>
#include "../dump/CppSDK/SDK.hpp"
#include "imgui.h"

namespace OSD {
    bool bShowOSD = true;
    ImFont* DroneFont = nullptr;

    void DrawTextOutlined(ImDrawList* drawList, ImFont* font, float fontSize, const ImVec2& pos, ImU32 color, const char* text) {
        ImU32 outlineColor = IM_COL32(0, 0, 0, 255);
        float d = 1.5f;
        drawList->AddText(font, fontSize, ImVec2(pos.x - d, pos.y), outlineColor, text);
        drawList->AddText(font, fontSize, ImVec2(pos.x + d, pos.y), outlineColor, text);
        drawList->AddText(font, fontSize, ImVec2(pos.x, pos.y - d), outlineColor, text);
        drawList->AddText(font, fontSize, ImVec2(pos.x, pos.y + d), outlineColor, text);
        drawList->AddText(font, fontSize, pos, color, text);
    }

    void Draw() {
        // --- ПЕРЕКЛЮЧЕНИЕ НА X ---
        if (ImGui::IsKeyPressed(ImGuiKey_X)) {
            bShowOSD = !bShowOSD;
        }

        if (!bShowOSD) return;

        // --- ЗАЩИТА (Проверка на наличие дрона в мире) ---
        auto World = SDK::UWorld::GetWorld();
        if (!World || !World->OwningGameInstance) return;

        auto PC = World->OwningGameInstance->LocalPlayers[0]->PlayerController;
        if (!PC || !PC->Pawn) return;

        // Если мы не в дроне - выходим, чтобы не было краша
        if (!PC->Pawn->IsA(SDK::ABP_Kamikaze_C::StaticClass())) return;

        // --- ЕСЛИ ПРОВЕРКИ ПРОЙДЕНЫ, ПОЛУЧАЕМ ДАННЫЕ ---
        auto Drone = static_cast<SDK::ABP_Kamikaze_C*>(PC->Pawn);

        ImGuiIO& io = ImGui::GetIO();
        ImDrawList* draw = ImGui::GetForegroundDrawList();
        ImVec2 s = io.DisplaySize;
        ImVec2 c = ImVec2(s.x * 0.5f, s.y * 0.5f);
        float fs = 24.0f;

        if (DroneFont == nullptr) {
            DroneFont = io.Fonts->AddFontFromFileTTF("font.ttf", fs);
            if (!DroneFont) DroneFont = io.FontDefault;
        }

        SDK::FVector loc = Drone->K2_GetActorLocation();
        SDK::FRotator rot = Drone->K2_GetActorRotation();
        float alt = loc.Z / 100.0f;
        float pitch = rot.Pitch;
        float roll = rot.Roll;

        ImU32 white = IM_COL32(255, 255, 255, 255);
        ImU32 green = IM_COL32(50, 255, 50, 255);
        char buf[256];

        // --- ГОРИЗОНТ ---
        float rRad = -roll * 0.4f * (3.14159f / 180.0f);
        float pOff = pitch * 1.2f;
        float lW = 100.0f, vP = 70.0f;
        ImVec2 p1 = ImVec2(c.x - cos(rRad) * lW, (c.y - vP - pOff) - sin(rRad) * lW);
        ImVec2 p2 = ImVec2(c.x + cos(rRad) * lW, (c.y - vP - pOff) + sin(rRad) * lW);
        draw->AddLine(p1, p2, IM_COL32(255, 255, 255, 160), 1.5f);

        // --- ВЕРХ ЛЕВО ---
        time_t n = time(0); tm* t = localtime(&n);
        snprintf(buf, sizeof(buf), "ACRO\n%02d:%02d\n-%.1f alt m", t->tm_hour, t->tm_min, alt);
        DrawTextOutlined(draw, DroneFont, fs, ImVec2(30, 30), white, buf);

        // --- ВЕРХ ЦЕНТР ---
        float v = (ImGui::IsKeyDown(ImGuiKey_W) || ImGui::IsKeyDown(ImGuiKey_S)) ? 20.9f : 21.8f;
        snprintf(buf, sizeof(buf), "%.1fV   %.2fV", v, v / 6.0f);
        ImVec2 ts = DroneFont->CalcTextSizeA(fs, FLT_MAX, 0.0f, buf);
        DrawTextOutlined(draw, DroneFont, fs, ImVec2((s.x - ts.x) * 0.5f, 30), white, buf);

        // --- ВЕРХ ПРАВО (ВОЗВРАЩЕНО) ---
        DrawTextOutlined(draw, DroneFont, fs, ImVec2(s.x - 220, 30), white, "НАРОДНЫЙ\nФРОНТ");

        // --- НИЗ ЛЕВО ---
        snprintf(buf, sizeof(buf), "link-ok\nrx: -5.612\ntx: -0.394");
        DrawTextOutlined(draw, DroneFont, fs, ImVec2(30, s.y - 180), white, buf);

        // --- НИЗ ПРАВО ---
        int thr = (ImGui::IsKeyDown(ImGuiKey_W) ? 85 : 17);
        snprintf(buf, sizeof(buf), "53.7 A\n10746 mAh\n28 %%\n\nгаз: %d %%\npitch: %.1f", thr, pitch);
        ts = DroneFont->CalcTextSizeA(fs, FLT_MAX, 0.0f, buf);
        DrawTextOutlined(draw, DroneFont, fs, ImVec2(s.x - ts.x - 30, s.y - ts.y - 80), white, buf);

        // --- САМЫЙ НИЗ (ЗЕЛЕНЫЙ - ВОЗВРАЩЕНО) ---
        snprintf(buf, sizeof(buf), "FW: 2.24               FPS: %.0f               SN: 571613792", io.Framerate);
        ts = DroneFont->CalcTextSizeA(fs, FLT_MAX, 0.0f, buf);
        DrawTextOutlined(draw, DroneFont, fs, ImVec2((s.x - ts.x) * 0.5f, s.y - 45), green, buf);
        DrawTextOutlined(draw, DroneFont, fs, ImVec2(30, s.y - 45), green, "БПЛА Пульт НСУ Запись Запись");

        // --- ПРИЦЕЛ ---
        float cs = 35.0f;
        draw->AddLine(ImVec2(c.x - cs, c.y), ImVec2(c.x + cs, c.y), white, 2.0f);
        draw->AddLine(ImVec2(c.x, c.y - cs), ImVec2(c.x, c.y + cs), white, 2.0f);
    }
}