//------------------------------------------------------------------------------
//  Emu/Main.cc
//------------------------------------------------------------------------------
#include "Pre.h"
#include "Core/Main.h"
#include "IO/IO.h"
#include "HttpFS/HTTPFileSystem.h"
#include "Core/Time/Clock.h"
#include "Gfx/Gfx.h"
#include "Dbg/Dbg.h"
#include "Input/Input.h"
#include "Common/CameraHelper.h"
#include "EmuCommon/KC85Emu.h"
#include "SceneRenderer.h"
#include "RayCheck.h"
#include "glm/gtc/matrix_transform.hpp"
#include <cstring>

using namespace Oryol;

class KC853App : public App {
public:
    AppState::Code OnInit();
    AppState::Code OnRunning();
    AppState::Code OnCleanup();

    // interactive elements
    enum {
        PowerOnButton,
        ResetButton,
        BaseDevice,
        Screen,
        Junost,
        Keyboard,
        TapeDeck,
        Jungle,
        Digger,
        Pengo,
        Boulderdash,
        Cave
    };

    void handleInput();
    void tooltip(const DisplayAttrs& disp, const char* str);

    TimePoint lapTime;
    KC85Emu kc85Emu;
    SceneRenderer scene;
    RayCheck rayChecker;
    glm::mat4 kcModelMatrix;
    CameraHelper camera;
};
OryolMain(KC853App);

//------------------------------------------------------------------------------
AppState::Code
KC853App::OnInit() {

    // setup Oryol modules
    IOSetup ioSetup;
    ioSetup.FileSystems.Add("http", HTTPFileSystem::Creator());
    ioSetup.Assigns.Add("kcc:", ORYOL_SAMPLE_URL);
    IO::Setup(ioSetup);
    auto gfxSetup = GfxSetup::WindowMSAA4(800, 512, "Emu");
    gfxSetup.DefaultPassAction = PassAction::Clear(glm::vec4(0.4f, 0.6f, 0.8f, 1.0f));
    Gfx::Setup(gfxSetup);
    Input::Setup();
    Dbg::Setup();
    Dbg::TextScale(2.0f, 2.0f);

    // setup the scene and ray collide checker
    this->scene.Setup(gfxSetup);
    this->rayChecker.Setup(gfxSetup);
    this->rayChecker.Add(Screen,        glm::vec3(50, 14, 38), glm::vec3(77, 35, 41));
    this->rayChecker.Add(Junost,        glm::vec3(40, 10, 42), glm::vec3(79, 39, 65));
    this->rayChecker.Add(PowerOnButton, glm::vec3(44, 1, 37), glm::vec3(49, 5, 41));
    this->rayChecker.Add(ResetButton,   glm::vec3(51, 1, 37), glm::vec3(56, 5, 41));
    this->rayChecker.Add(BaseDevice,    glm::vec3(40, 1, 39), glm::vec3(79, 8, 65));
    this->rayChecker.Add(Keyboard,      glm::vec3(44, 1, 18), glm::vec3(75, 2, 33));
    this->rayChecker.Add(Jungle,        glm::vec3(26, 1, 17), glm::vec3(34, 2, 22));
    this->rayChecker.Add(Digger,        glm::vec3(19, 7, 46), glm::vec3(27, 8, 51));
    this->rayChecker.Add(Pengo,         glm::vec3(15, 1, 13), glm::vec3(23, 2, 18));
    this->rayChecker.Add(Boulderdash,   glm::vec3(21, 1, 4),  glm::vec3(29, 2, 9));
    this->rayChecker.Add(Cave,          glm::vec3(14, 0, 28), glm::vec3(33, 6, 40));
    this->rayChecker.Add(TapeDeck,      glm::vec3(14, 0, 41), glm::vec3(33, 6, 54));

    // setup the camera helper
    this->camera.Setup(false);
    this->camera.Center = glm::vec3(63.0f, 25.0f, 40.0f);
    this->camera.MaxCamDist = 200.0f;
    this->camera.Distance = 80.0f;
    this->camera.Orbital = glm::vec2(glm::radians(10.0f), glm::radians(160.0f));

    // setup the KC emulator
    this->kc85Emu.Setup(gfxSetup);
    this->lapTime = Clock::Now();

    glm::mat4 m = glm::rotate(glm::mat4(1.0f), glm::radians(180.0f), glm::vec3(0.0f, 1.0f, 0.0f));
    m = glm::rotate(m, -glm::radians(90.0f), glm::vec3(1.0f, 0.0f, 0.0f));
    m = glm::translate(m, glm::vec3(-63.0f, 39.0f, 25.0f));
    m = glm::scale(m, glm::vec3(28.0f, 1.0f, 22.0f));
    this->kcModelMatrix = m;

    return App::OnInit();
}

//------------------------------------------------------------------------------
AppState::Code
KC853App::OnRunning() {
    this->camera.Update();
    this->handleInput();

    // update KC85 emu
    this->kc85Emu.Update(Clock::LapTime(this->lapTime));

    // render the voxel scene and emulator screen
    Gfx::BeginPass();
    this->scene.Render(this->camera.ViewProj);
    this->kc85Emu.Render(this->camera.ViewProj * this->kcModelMatrix);
//    this->rayChecker.RenderDebug(this->camera.ViewProj);
    Dbg::DrawTextBuffer();
    Gfx::EndPass();
    Gfx::CommitFrame();
    return Gfx::QuitRequested() ? AppState::Cleanup : AppState::Running;
}

//------------------------------------------------------------------------------
AppState::Code
KC853App::OnCleanup() {
    Input::Discard();
    IO::Discard();
    Gfx::Discard();
    return App::OnCleanup();
}

//------------------------------------------------------------------------------
void
KC853App::handleInput() {
    if (Input::MouseAttached()) {
        glm::vec2 screenSpaceMousePos = Input::MousePosition();
        const bool lmb = Input::MouseButtonDown(MouseButton::Left);
        const DisplayAttrs& disp = Gfx::DisplayAttrs();
        screenSpaceMousePos.x /= float(disp.FramebufferWidth);
        screenSpaceMousePos.y /= float(disp.FramebufferHeight);
        glm::mat4 invView = glm::inverse(this->camera.View);
        int hit = this->rayChecker.Test(screenSpaceMousePos, invView, this->camera.InvProj);
        switch (hit) {
            case PowerOnButton:
                if (lmb) {
                    this->kc85Emu.TogglePower();
                }
                if (this->kc85Emu.SwitchedOn()) {
                    this->tooltip(disp, "SWITCH KC85/3 OFF");
                }
                else {
                    this->tooltip(disp, "SWITCH KC85/3 ON");
                }
                break;
            case ResetButton:
                if (lmb) {
                    this->kc85Emu.Reset();
                }
                this->tooltip(disp, "RESET KC85/3");
                break;
            case BaseDevice:
                this->tooltip(disp, "A KC85/3, EAST GERMAN 8-BIT COMPUTER");
                break;
            case Screen:
                // prevent Junost tooltip when mouse is over screen
                break;
            case Junost:
                this->tooltip(disp, "A YUNOST 402B, SOVIET TV");
                break;
            case Keyboard:
                this->tooltip(disp, "TYPE SOMETHING!");
                break;
            case TapeDeck:
                this->tooltip(disp, "AN 'LCR-C DATA' TAPE DECK");
                break;
            case Jungle:
                if (lmb) {
                    this->kc85Emu.StartGame("Jungle");
                }
                this->tooltip(disp, "PLAY JUNGLE!");
                break;
            case Digger:
                if (lmb) {
                    this->kc85Emu.StartGame("Digger");
                }
                this->tooltip(disp, "PLAY DIGGER!");
                break;
            case Pengo:
                if (lmb) {
                    this->kc85Emu.StartGame("Pengo");
                }
                this->tooltip(disp, "PLAY PENGO!");
                break;
            case Boulderdash:
                if (lmb) {
                    this->kc85Emu.StartGame("Boulderdash");
                }
                this->tooltip(disp, "PLAY BOULDERDASH!");
                break;
            case Cave:
                if (lmb) {
                    this->kc85Emu.StartGame("Cave");
                }
                this->tooltip(disp, "PLAY CAVE!");
                break;
            default:
                if (!this->kc85Emu.SwitchedOn()) {
                    this->tooltip(disp, "EXPLORE!");
                }
                break;
        }
    }
}

//------------------------------------------------------------------------------
void
KC853App::tooltip(const DisplayAttrs& disp, const char* str) {
    o_assert_dbg(str);
    
    // center the text
    int center = (disp.FramebufferWidth / 16) / 2;
    int len = int(std::strlen(str));
    int posX = center - (len/2);
    if (posX < 0) {
        posX = 0;
    }
    Dbg::CursorPos(uint8_t(posX), 2);
    Dbg::Print(str);
}
